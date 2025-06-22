"""Domain classes.

"""
from __future__ import annotations
__author__ = 'Paul Landes'
from typing import Tuple, Iterable, Any, Union, Optional, Type, Callable
from dataclasses import dataclass, field
from abc import abstractmethod, ABCMeta
import logging
import traceback
import pandas as pd
from zensols.util import APIError
from zensols.persist import resource

logger = logging.getLogger(__name__)


class DBError(APIError):
    """"Raised for all :mod:`zensols.db`` related errors.

    """
    pass


class connection(resource):
    """Annotation used to create and dispose of DB-API connections.

    """
    def __init__(self):
        super().__init__('_create_connection', '_dispose_connection')


class _CursorIterator(object):
    """Iterates throw the rows of the database using a cursor.

    """
    def __init__(self, mng: ConnectionManager, conn: Any, cursor: Any):
        """

        :param mng: the connection manager to regulate database resources

        :param conn: the connection to the database

        :param cursor: the cursor to the database

        """
        self._mng = mng
        self._conn = conn
        self._cursor = cursor

    def __iter__(self) -> _CursorIterator:
        return self

    def __next__(self):
        if self._cursor is None:
            raise StopIteration
        try:
            return next(self._cursor)
        except StopIteration:
            try:
                self.dispose()
            finally:
                raise StopIteration

    def dispose(self):
        if self._mng is not None:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('closing cursor iterable')
            self._mng._do_dispose_connection = True
            self._cursor.close()
            self._mng.dispose(self._conn)
            self._mng = None
            self._conn = None
            self._cursor = None


@dataclass
class AbstractDbPersister(object, metaclass=ABCMeta):
    """An abstract class to CRUD data with basic operations and a connection to
    the database.

    """
    conn_manager: ConnectionManager = field()
    """Used to create DB-API connections."""

    @connection()
    def execute(self, conn: Any, sql: str, params: Tuple[Any, ...] = (),
                row_factory: Union[str, Callable] = None,
                map_fn: Callable = None) -> \
            Tuple[Union[dict, tuple, pd.DataFrame]]:
        """Execute SQL on a database connection.

        The ``row_factory`` tells the method how to interpret the row data in
        to an object that's returned.  It can be one of:

            * ``tuple``: tuples (the default)
            * ``dict``: for dictionaries
            * ``pandas``: for a :class:`pandas.DataFrame`
            * otherwise: a function or class

        Compare this with ``map_fn``, which transforms the data that's given to
        the ``row_factory``.

        :param sql: the string SQL to execute

        :param params: the parameters given to the SQL statement (populated
                       with ``?``) in the statement

        :param row_factory: ``tuple``, ``dict``, ``pandas`` or a function

        :param map_fn: a function that transforms row data given to the
                       ``row_factory``

        """
        row_factory = self.row_factory if row_factory is None else row_factory
        return self.conn_manager.execute(
            conn, sql, params, row_factory, map_fn)

    @connection()
    def _execute_iterate(self, conn: Any, sql: str, name: str,
                         params: Tuple[Any, ...]):
        if sql is None and name is None:
            raise DBError('Both sql string and name can not be None')
        if sql is None:
            self._check_entry(name)
            sql = self.sql_entries[name]
        cur = self.conn_manager._create_cursor(conn, sql, params)
        self.conn_manager._do_dispose_connection = False
        return _CursorIterator(self.conn_manager, conn, cur)


class cursor(object):
    """Iterate through rows of a database.  The connection is automatically
    closed once out of scope.

    Example::

        config_factory: ConfigFactory = ...
        persister: DbPersister = config_factory.instance('person_db_persister')
        with cursor(persister, name='select_people') as c:
            for row in c:
                print(row)

    """
    def __init__(self, persister: AbstractDbPersister, sql: str = None,
                 name: str = None, params: Tuple[Any, ...] = ()):
        """Initialize with either ``name`` or ``sql`` (only one should be
        ``None``).

        :param persister: used to execute the SQL and obtain the cursor

        :param sql: the string SQL to execute

        :param name: the named SQL query in the :obj:`.DbPersister.sql_file`

        :param params: the parameters given to the SQL statement (populated
                       with ``?``) in the statement

        """
        self._curiter = persister._execute_iterate(
            sql=sql,
            name=name,
            params=params)

    def __enter__(self) -> Iterable[Any]:
        return self._curiter

    def __exit__(self, cls: Type[Exception], value: Optional[Exception],
                 trace: traceback):
        self._curiter.dispose()


@dataclass
class ConnectionManager(object, metaclass=ABCMeta):
    """Instance DB-API connection lifecycle.

    """
    def __post_init__(self):
        self._do_dispose_connection = True

    def register_persister(self, persister: AbstractDbPersister):
        """Register the persister used for this connection manager.

        :param persister: the persister used for connection management

        """
        self.persister = persister

    @abstractmethod
    def create(self) -> Any:
        """Create a connection to the database.

        """
        pass

    def dispose(self, conn: Any):
        """Close the connection to the database.

        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'connection manager: closing {conn}')
        if self._do_dispose_connection:
            conn.close()

    @abstractmethod
    def drop(self) -> bool:
        """Remove all objects from the database or the database itself.

        For SQLite, this deletes the file.  In database implementations, this
        might drop all objects from the database.  Regardless, it is expected
        that ``create`` is able to recreate the database after this action.

        :return: whether the database was dropped

        """
        pass

    def _to_dataframe(self, res: Iterable[Any], cursor: Any) -> pd.DataFrame:
        """Return a Pandas dataframe from the results given by the database.

        :param res: the database results row by row

        :param cursor: the database cursor object, which has a ``description``
                       attribute

        """
        cols = tuple(map(lambda d: d[0], cursor.description))
        return pd.DataFrame(res, columns=cols)

    def execute(self, conn: Any, sql: str, params: Tuple[Any, ...],
                row_factory: Union[str, Callable],
                map_fn: Callable) -> Tuple[Union[dict, tuple, pd.DataFrame]]:
        """Execute SQL on a database connection.

        The ``row_factory`` tells the method how to interpret the row data in
        to an object that's returned.  It can be one of:

            * ``tuple``: tuples (the default)

            * ``identity``: return the unmodified form from the database

            * ``dict``: for dictionaries

            * ``pandas``: for a :class:`pandas.DataFrame`

            * otherwise: a function or class

        Compare this with ``map_fn``, which transforms the data that's given to
        the ``row_factory``.

        :param conn: the connection object with the database

        :param sql: the string SQL to execute

        :param params: the parameters given to the SQL statement (populated
                       with ``?``) in the statement

        :param row_factory: ``tuple``, ``dict``, ``pandas`` or a function

        :param map_fn: a function that transforms row data given to the
                       ``row_factory``

        :see: :meth:`.DbPersister.execute`.

        """
        def dict_row_factory(cursor: Any, row: Tuple[Any, ...]):
            return dict(map(lambda x: (x[1][0], row[x[0]]),
                            enumerate(cursor.description)))

        conn.row_factory = {
            'dict': dict_row_factory,
            'tuple': lambda cursor, row: row,
            'identity': lambda cursor, row: row,
            'pandas': None,
        }.get(
            row_factory,
            lambda cursor, row: row_factory(*row)
        )
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'sql: <{sql}>, params: {params}')
        cur: Any = conn.cursor()
        try:
            res = cur.execute(sql, params)
            if map_fn is not None:
                res = map(map_fn, res)
            if row_factory == 'pandas':
                res = self._to_dataframe(res, cur)
            if conn.row_factory is not None:
                res = tuple(res)
            return res
        finally:
            cur.close()

    def _create_cursor(self, conn: Any, sql: str,
                       params: Tuple[Any, ...]) -> Any:
        """Create a cursor object from connection ``conn``."""
        cur: Any = conn.cursor()
        cur.execute(sql, params)
        return cur

    def execute_no_read(self, conn: Any, sql: str,
                        params: Tuple[Any, ...]) -> int:
        """Return database level information such as row IDs rather than the
        results of a query.  Use this when inserting data to get a row ID.

        :param conn: the connection object with the database

        :param sql: the SQL statement used on the connection's cursor

        :param params: the parameters given to the SQL statement (populated
                       with ``?``) in the statement

        :see: :meth:`.DbPersister.execute_no_read`.

        """
        cur = conn.cursor()
        try:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'sql: {sql}, params: {params}')
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid
        finally:
            cur.close()

    def insert_rows(self, conn: Any, sql: str, rows: Iterable[Any],
                    errors: str, set_id_fn: Callable,
                    map_fn: Callable) -> int:
        """Insert a tuple of rows in the database and return the current row ID.

        :param rows: a sequence of tuples of data (or an object to be
                     transformed, see ``map_fn`` in column order of the SQL
                     provided by the entry :obj:`insert_name`

        :param errors: if this is the string ``raise`` then raise an error on
                       any exception when invoking the database execute,
                       otherwise use ``ignore`` to ignore errors

        :param set_id_fn: a callable that is given the data to be inserted and
                          the row ID returned from the row insert as parameters

        :param map_fn: if not ``None``, used to transform the given row in to a
                       tuple that is used for the insertion

        :return: the ``rowid`` of the last row inserted

        See :meth:`.InsertableBeanDbPersister.insert_rows`.

        """
        cur = conn.cursor()
        try:
            for row in rows:
                if map_fn is not None:
                    org_row = row
                    row = map_fn(row)
                if errors == 'raise':
                    cur.execute(sql, row)
                elif errors == 'ignore':
                    try:
                        cur.execute(sql, row)
                    except Exception as e:
                        logger.error(f'could not insert row ({len(row)})', e)
                else:
                    raise DBError(f'unknown errors value: {errors}')
                if set_id_fn is not None:
                    set_id_fn(org_row, cur.lastrowid)
        finally:
            conn.commit()
            cur.close()
        return cur.lastrowid
