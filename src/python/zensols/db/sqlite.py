"""Convenience wrapper for the Python DB-API library, and some specificly for
the SQLite library.

"""
__author__ = 'Paul Landes'

import logging
from pathlib import Path
import sqlite3
from zensols.actioncli import ConfigFactory
from zensols.db import (
    DbPersister,
    ConnectionFactory,
    BeanDbPersister,
)

logger = logging.getLogger(__name__)


class SqliteConnectionFactory(ConnectionFactory):
    """An SQLite connection factory.

    """
    def __init__(self, db_file: Path, persister: DbPersister,
                 create_db: bool = True):
        """Initialize.

        :param db_file: the SQLite database file to read or create
        :param persister: the persister that will use this connection factory
                          (needed to get the initialization DDL SQL)

        """
        super(SqliteConnectionFactory, self).__init__()
        self.db_file = db_file
        self.persister = persister
        self.create_db = create_db

    def create(self):
        db_file = self.db_file
        logger.debug(f'creating connection to {db_file}')
        created = False
        if not db_file.exists():
            if not self.create_db:
                raise ValueError(f'database file {db_file} does not exist')
            if not db_file.parent.exists():
                logger.info(f'creating sql db directory {db_file.parent}')
                db_file.parent.mkdir(parents=True)
            logger.info(f'creating sqlite db file: {db_file}')
            created = True
        types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        conn = sqlite3.connect(str(db_file.absolute()), detect_types=types)
        if created:
            logger.info(f'initializing database...')
            for sql in self.persister.parser.get_init_db_sqls():
                logger.debug(f'invoking sql: {sql}')
                conn.execute(sql)
                conn.commit()
        return conn

    def delete_file(self):
        """Delete the SQLite database file from the file system.

        """
        logger.info(f'deleting: {self.db_file}')
        if self.db_file.exists():
            self.db_file.unlink()
            return True
        return False


class ConfigSqliteDbPersisterFactory(ConfigFactory):
    """A factory that creates SQLite based ``DbPersister``.

    The following parameters are needed (in addition to the class name):
      * sql_file: the text file that contains the SQL statements
      * db_file: the path to the SQLite data file
      * insert_name: the entry name of the SQL used to insert data
      * select_name: the entry name of the SQL used to select/return data

    """
    INSTANCE_CLASSES = {}

    def __init__(self, config):
        super(ConfigSqliteDbPersisterFactory, self).__init__(
            config, '{name}_db_persister')

    def _class_name_params(self, name):
        class_name, params = super(ConfigSqliteDbPersisterFactory, self).\
            _class_name_params(name)
        params['sql_file'] = Path(params['sql_file'])
        params['conn_factory'] = SqliteConnectionFactory(
            Path(params['db_file']), None)
        del params['db_file']
        return class_name, params

    def _instance(self, cls, *args, **kwargs):
        inst = super(ConfigSqliteDbPersisterFactory, self)._instance(
            cls, *args, **kwargs)
        inst.conn_factory.persister = inst
        return inst


ConfigSqliteDbPersisterFactory.register(BeanDbPersister)
