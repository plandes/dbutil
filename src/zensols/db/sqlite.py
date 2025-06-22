"""Convenience wrapper for the Python DB-API library, and some specificly for
the SQLite library.

"""
__author__ = 'Paul Landes'

import logging
from dataclasses import dataclass, field
from pathlib import Path
import sqlite3
from . import DBError, ConnectionManager, DbStash

logger = logging.getLogger(__name__)


@dataclass
class SqliteConnectionManager(ConnectionManager):
    """An SQLite connection factory.

    """
    db_file: Path = field()
    """The SQLite database file to read or create."""

    create_db: bool = field(default=True)
    """If ``True``, create the database if it does not already exist.
    Otherwise, :class:`.DBError` is raised (see :meth:`create`).

    """
    def create(self) -> sqlite3.Connection:
        """Create a connection by accessing the SQLite file.

        :raise DBError: if the SQLite file does not exist (caveat see
                        :`obj:create_db`)

        """
        db_file: Path = self.db_file
        do_create: bool = False
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'creating connection to {db_file}')
        if not db_file.exists():
            if not self.create_db:
                raise DBError(f'database file {db_file} does not exist')
            if not db_file.parent.exists():
                if logger.isEnabledFor(logging.INFO):
                    logger.info(f'creating sql db directory {db_file.parent}')
                db_file.parent.mkdir(parents=True)
            if logger.isEnabledFor(logging.INFO):
                logger.info(f'creating sqlite db file: {db_file}')
            do_create = True
        types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        conn = sqlite3.connect(str(db_file.absolute()), detect_types=types)
        if do_create:
            logger.info('initializing database...')
            for sql in self.persister.parser.get_init_db_sqls():
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f'invoking sql: {sql}')
                conn.execute(sql)
                conn.commit()
        return conn

    def drop(self) -> bool:
        """Delete the SQLite database file from the file system."""
        logger.info(f'deleting: {self.db_file}')
        if self.db_file.exists():
            self.db_file.unlink()
            return True
        return False


@dataclass
class SqliteAttachConnectionManager(ConnectionManager):
    """An SQLite connection factory that attaches a file as a database.

    """
    db_file: Path = field()
    """The SQLite database file to read or create."""

    database_name: str = field()
    """The name of the database used to attach to :obj:`db_file`."""

    def create(self) -> sqlite3.Connection:
        """Create a connection as an attached database to a file."""
        conn = sqlite3.connect(':memory:')
        conn.execute(
            f'ATTACH DATABASE ? AS {self.database_name}',
            (str(self.db_file),))
        return conn

    def drop(self) -> bool:
        """Dropping a memory SQLite connection is not supported."""
        return False


@dataclass
class SqliteDbStash(DbStash):
    """A :class:`~zensols.persist.domain.Stash` implementation that uses an
    SQLite database to store data.
    """
    path: Path = field(default=None)
    """The directory of where to store the files."""

    def _create_connection_manager(self) -> ConnectionManager:
        if self.path is None:
            raise DBError(f'No configured path for {type(self)} stash')
        return SqliteConnectionManager(self.path)
