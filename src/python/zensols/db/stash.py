"""Adapt a database centric :class:`.DbPersister` to a general
:class:`~zensols.persist.Stash` container.

"""
__author__ = 'Paul Landes'

from typing import Any, Iterable
from dataclasses import dataclass
from zensols.persist import Stash
from . import DBError, BeanDbPersister


@dataclass
class BeanStash(Stash):
    """A stash that uses a backing DB-API backed :class:`BeanDbPersister`.

    """
    def __init__(self, persister: BeanDbPersister):
        self.persister = persister

    def load(self, name: str) -> Any:
        return self.persister.get_by_id(int(name))

    def exists(self, name: str) -> bool:
        return self.persister.exists(int(name))

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
        self.persister.delete(name)

    def keys(self) -> Iterable[str]:
        return self.persister.get_keys()

    def __len__(self) -> int:
        return self.persister.get_count()
