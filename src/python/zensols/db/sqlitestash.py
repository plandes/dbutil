"""Contains classes to support a binary or text data value SQLite store
:class:`~zensols.persist.domain.Stash`.

"""
__author__ = 'Paul Landes'

from typing import Any, Iterable, Union
from dataclasses import dataclass, field
from abc import ABCMeta, abstractmethod
import logging
import pickle
from io import BytesIO
from pathlib import Path
from io import StringIO
from zensols.persist import persisted, Stash
from zensols.config import IniConfig, ImportConfigFactory
from . import DBError, ConnectionManager, BeanDbPersister

logger = logging.getLogger(__name__)


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
    """A :class:`~zensols.persist.domain.Stash` implementation that uses an
    SQLite database to store data.  It creates a single table with only two
    columns: one for the (string) key and the other for the values.

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
        config: str = _DBSTASH_PERSISTER_CONFIG
        fac = ImportConfigFactory(IniConfig(StringIO(config)))
        return fac(
            name='db_persister',
            conn_manager=self._create_connection_manager())

    def load(self, name: str) -> Any:
        inst: Any = self.persister.get_by_id(name)[0]
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
class SqliteDbStash(DbStash):
    path: Path = field(default=None)
    """The directory of where to store the files."""

    def _create_connection_manager(self) -> ConnectionManager:
        from .sqlite import SqliteConnectionManager
        if self.path is None:
            raise DBError(f'No configured path for {type(self)} stash')
        return SqliteConnectionManager(self.path)
