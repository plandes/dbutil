"""Connection pool.

"""
__author__ = 'Paul Landes'

from typing import List, Any
from dataclasses import dataclass, field
import logging
from .conn import AbstractDbPersister, ConnectionManager

logger = logging.getLogger(__name__)


@dataclass
class PooledConnectionManager(ConnectionManager):
    """Pools database connections.

    """
    delegate: ConnectionManager = field()
    """The delegate manager that controls the lifecycle of pooled connections.

    """
    size: int = field(default=1)
    """The size of the pool."""

    def __post_init__(self):
        super().__post_init__()
        self._pool: List[Any] = []

    def register_persister(self, persister: AbstractDbPersister):
        super().register_persister(persister)
        self.delegate.register_persister(persister)

    @property
    def is_empty(self) -> bool:
        return len(self) == 0

    @property
    def is_full(self) -> bool:
        return len(self) >= self.size

    def create(self) -> Any:
        conn: Any
        if self.is_empty:
            conn = self.delegate.create()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'creating connection: size now: {len(self)}')
        else:
            conn = self._pool.pop()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'popped connection, size now: {len(self)}')
        return conn

    def dispose(self, conn: Any):
        if self.is_full:
            self.delegate.dispose(conn)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'disposed connection: size now: {len(self)}')
        else:
            self._pool.append(conn)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'caching connection: size now: {len(self)}')

    def dispose_all(self):
        """Dispose of all connections."""
        conn: Any
        for conn in self._pool:
            self.delegate.dispose(conn)
        self._pool.clear()

    def drop(self) -> bool:
        self.delegate.drop()

    def __len__(self) -> int:
        return len(self._pool)
