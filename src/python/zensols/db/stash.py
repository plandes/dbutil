"""Adapt a database centric :class:`.DbPersister` to a general
:class:`~zensols.persist.Stash` container.

"""
__author__ = 'Paul Landes'

from typing import Any, Iterable, Tuple, Optional, Union
from dataclasses import dataclass, field
from abc import ABCMeta, abstractmethod
import pickle
from io import BytesIO
from io import StringIO
from zensols.persist import persisted, Stash
from zensols.config import IniConfig, ImportConfigFactory
from . import DBError, ConnectionManager, BeanDbPersister

_DBSTASH_PERSISTER_CONFIG: str = """\
[db_persister]
class_name = zensols.db.BeanDbPersister
sql_file = resource(zensols.db): resources/sqlite-stash.sql
insert_name = insert_item
select_by_id_name = select_item_by_id
select_exists_name = select_item_exists_by_id
update_name = update_item
delete_name = delete_item
keys_name = entries_ids
count_name = entries_count
"""


class DbStashEncoderDecoder(object):
    """Encodes and decodes data for :class:`.SqliteStash`.

    """
    def encode(self, data: Any) -> Union[str, bytes]:
        return data

    def decode(self, data: Union[str, bytes]) -> Any:
        return data


class PickleDbStashEncoderDecoder(DbStashEncoderDecoder):
    """An implementation that encodes and decodes using :mod:`pickle`.

    """
    def encode(self, data: Any) -> Union[str, bytes]:
        bio = BytesIO()
        pickle.dump(data, bio)
        return bio.getvalue()

    def decode(self, data: Union[str, bytes]) -> Any:
        bio = BytesIO(data)
        bio.seek(0)
        return pickle.load(bio)


@dataclass
class DbStash(Stash, metaclass=ABCMeta):
    """A relational database to store stash keys and values.  It creates a
    single table with only two columns: one for the (string) key and the other
    for the values.

    """
    encoder_decoder: DbStashEncoderDecoder = field(
        default_factory=PickleDbStashEncoderDecoder)
    """Used to encode and decode the data with the SQLite database.  To use
    binary data, set this to an instance of

    This should be set to:

      * :class:`.DbStashEncoderDecoder`: store text values
      * :class:`.PickleDbStashEncoderDecoder`: store binary data (default)
      * :mod:`jsonpickle`: store JSON (needs ``pip install jsonpickle``); use
        ``encoder_decoder = eval({'import': ['jsonpickle']}): jsonpickle`` in
        application configurations

    You can write your own by extending :class:`.DbStashEncoderDecoder`.

    """
    @abstractmethod
    def _create_connection_manager(self) -> ConnectionManager:
        pass

    @property
    @persisted('_persister')
    def persister(self) -> BeanDbPersister:
        """The persister used to interface with the database."""
        config: str = _DBSTASH_PERSISTER_CONFIG
        fac = ImportConfigFactory(IniConfig(StringIO(config)))
        return fac(name='db_persister',
                   conn_manager=self._create_connection_manager())

    def load(self, name: str) -> Any:
        row: Tuple[Any] = self.persister.get_by_id(name)
        if row is not None:
            inst: Any = row[0]
            return self.encoder_decoder.decode(inst)

    def exists(self, name: str) -> bool:
        return self.persister.exists(name)

    def dump(self, name: str, inst: Any):
        """Since this implementation can let the database auto-increment the
        unique/primary key, beware of "changing" keys.

        :raises DBError: if the key changes after inserted it will raise a
                ``DBError``; for this reason, it's best to pass ``None`` as
                ``name``

        """
        inst: Union[str, bytes] = self.encoder_decoder.encode(inst)
        if self.exists(name):
            self.persister.update_row(name, inst)
        else:
            self.persister.insert_row(name, inst)
        return inst

    def delete(self, name: str):
        self.persister.delete(name)

    def keys(self) -> Iterable[str]:
        return map(str, self.persister.get_keys())

    def clear(self):
        self.persister.conn_manager.drop()

    def __len__(self) -> int:
        return self.persister.get_count()


@dataclass
class BeanStash(Stash):
    """A stash that uses a backing DB-API backed :class:`BeanDbPersister`.

    """
    persister: BeanDbPersister = field()
    """The delegate bean persister."""

    def load(self, name: str) -> Any:
        return self.persister.get_by_id(int(name))

    def exists(self, name: str) -> bool:
        try:
            name = int(name)
        except ValueError:
            # assume only number IDs
            return False
        return self.persister.exists(name)

    def dump(self, name: str, inst: Any):
        """Since this implementation can let the database auto-increment the
        unique/primary key, beware of "changing" keys.

        :raises DBError: if the key changes after inserted it will raise a
                ``DBError``; for this reason, it's best to pass ``None`` as
                ``name``

        """
        if name is not None:
            id = int(name)
            inst.id = id
        else:
            id = inst.id
        if id is not None and self.exists(id):
            self.persister.update(inst)
        else:
            self.persister.insert(inst)
        if id is not None and inst.id != id:
            raise DBError(f'unexpected key change: {inst.id} != {id}')
        return inst

    def delete(self, name: str):
        self.persister.delete(int(name))

    def keys(self) -> Iterable[str]:
        return map(str, self.persister.get_keys())

    def __len__(self) -> int:
        return self.persister.get_count()


@dataclass
class AlternateKeyBeanStash(BeanStash):
    """A stash that uses another key rather than some unique primary key
    (i.e. rowid for SQLite).  It does this by looking up the alternate key in
    some other column and resolves to the unique primary key.

    The domain and range of the function (:meth:`_key_to_id`) that maps
    alternate keys to unique primary keys ate strings.

    .. document private functions
    .. automethod:: _key_to_id

    """
    key_to_id_name: str = field()
    """The select method SQL name that selects the unique priamry to the
    alterante key.

    """
    keys_name: str = field()
    """The select method SQL name that selects the alternate in :meth:`keys`."""

    def _key_to_id(self, name: str) -> Optional[str]:
        """Maps alternate keys to unique primary keys.

        :param name: the alternate key, which is usually a more client friendly
                     string

        :return: the unique primary key in the database (usually an
                 :class:`int`)

        """
        row: Tuple = self.persister.execute_singleton_by_name(
            self.key_to_id_name, params=(name,),
            row_factory='identity')
        if row is not None:
            return str(row[0])

    def load(self, name: str) -> Any:
        return super().load(self._key_to_id(name))

    def exists(self, name: str) -> bool:
        id: Optional[Any] = self._key_to_id(name)
        return id is not None

    def dump(self, name: str, inst: Any):
        return super().dump(self._key_to_id(name), inst)

    def delete(self, name: str):
        return super().delete(self._key_to_id(name))

    def keys(self) -> Iterable[str]:
        return set(self.persister.execute_by_name(
            self.keys_name, row_factory='identity',
            map_fn=lambda r: r[0]))
