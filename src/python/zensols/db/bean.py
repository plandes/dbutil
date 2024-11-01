"""Basic CRUD utility classes

"""
__author__ = 'Paul Landes'
from typing import Dict, Any, Tuple, Union, Callable, Iterable, Type, List
from dataclasses import dataclass, field, fields
from abc import ABCMeta
import logging
from pathlib import Path
import pandas as pd
from zensols.persist import chunks
from zensols.db import DynamicDataParser
from .conn import connection, DBError, AbstractDbPersister

logger = logging.getLogger(__name__)


@dataclass
class DbPersister(AbstractDbPersister):
    """CRUDs data to/from a DB-API connection.

    """
    sql_file: Path = field(default=None)
    """The text file containing the SQL statements (see
    :class:`DynamicDataParser`).

    """
    row_factory: Union[str, Type] = field(default='tuple')
    """The default method by which data is returned from ``execute_*`` methods.

    :see: :meth:`execute`.

    """
    def __post_init__(self):
        self.parser = self._create_parser(self.sql_file)
        self.conn_manager.register_persister(self)

    def _create_parser(self, sql_file: Path) -> DynamicDataParser:
        return DynamicDataParser(sql_file)

    @property
    def _sql_file(self) -> Path:
        return self._sql_file_val

    @_sql_file.setter
    def _sql_file(self, sql_file: Path):
        self._sql_file_val = sql_file
        if hasattr(self, 'parser'):
            self.parser.dd_path = sql_file

    @property
    def sql_entries(self) -> Dict[str, str]:
        """Return a dictionary of names -> SQL statements from the SQL file.

        """
        return self.parser.sections

    @property
    def metadata(self) -> Dict[str, str]:
        """Return the metadata associated with the SQL file.

        """
        return self.parser.metadata

    def _create_connection(self):
        """Create a connection to the database.

        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('creating connection')
        return self.conn_manager.create()

    def _dispose_connection(self, conn: Any):
        """Close the connection to the database.

        :param conn: the connection to release

        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'closing connection {conn}')
        self.conn_manager.dispose(conn)

    def _check_entry(self, name: str):
        if name is None:
            raise DBError('No defined SQL entry for persist function ' +
                          f"in SQL file '{self.sql_file}'")
        if len(name) == 0:
            raise DBError('Non-optional entry not provided ' +
                          f"in SQL file '{self.sql_file}'")
        if name not in self.sql_entries:
            raise DBError(f"No entry '{name}' found in SQL configuration " +
                          f"in SQL file '{self.sql_file}'")

    def _get_entry(self, name: str):
        self._check_entry(name)
        return self.sql_entries[name]

    def execute_by_name(self, name: str, params: Tuple[Any] = (),
                        row_factory: Union[str, Callable] = None,
                        map_fn: Callable = None):
        """Just like :meth:`execute` but look up the SQL statement to execute on
        the database connection.

        The ``row_factory`` tells the method how to interpret the row data in
        to an object that's returned.  It can be one of:

            * ``tuple``: tuples (the default)
            * ``dict``: for dictionaries
            * ``pandas``: for a :class:`pandas.DataFrame`
            * otherwise: a function or class

        Compare this with ``map_fn``, which transforms the data that's given to
        the ``row_factory``.

        :param name: the named SQL query in the :obj:`sql_file`

        :param params: the parameters given to the SQL statement (populated
                       with ``?``) in the statement

        :param row_factory: ``tuple``, ``dict``, ``pandas`` or a function

        :param map_fn: a function that transforms row data given to the
                       ``row_factory``

        :see: :meth:`execute`

        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'name: <{name}>, params: {params}')
        self._check_entry(name)
        sql = self.sql_entries[name]
        return self.execute(sql, params, row_factory, map_fn)

    def execute_singleton_by_name(self, *args, **kwargs):
        """Just like :meth:`execute_by_name` except return only the first item
        or ``None`` if no results.

        """
        res = self.execute_by_name(*args, **kwargs)
        if len(res) > 0:
            return res[0]

    @connection()
    def execute_sql_no_read(self, conn: Any, sql: str,
                            params: Tuple[Any] = ()) -> int:
        """Execute SQL and return the database level information such as row IDs
        rather than the results of a query.  Use this when inserting data to get
        a row ID.

        """
        return self.conn_manager.execute_no_read(conn, sql, params)

    @connection()
    def execute_no_read(self, conn: Any, entry_name: str,
                        params: Tuple[Any] = ()) -> int:
        """Just like :meth:`execute_by_name`, but return database level
        information such as row IDs rather than the results of a query.  Use
        this when inserting data to get a row ID.

        :param entry_name: the key in the SQL file whose value is used as the
                           statement

        :param capture_rowid: if ``True``, return the last row ID from the
                              cursor

        :see: :meth:`execute_sql_no_read`

        """
        self._check_entry(entry_name)
        sql = self.sql_entries[entry_name]
        return self.conn_manager.execute_no_read(conn, sql, params)


# keep the dataclass semantics, but allow for a setter
DbPersister.sql_file = DbPersister._sql_file


@dataclass
class Bean(object, metaclass=ABCMeta):
    """A container class like a Java *bean*.

    """
    def get_attr_names(self) -> Tuple[str]:
        """Return a list of string attribute names.

        """
        return tuple(map(lambda f: f.name, fields(self)))

    def get_attrs(self) -> Dict[str, Any]:
        """Return a dict of attributes that are meant to be persisted.

        """
        return {n: getattr(self, n) for n in self.get_attr_names()}

    def get_row(self) -> Tuple[Any]:
        """Return a row of data meant to be printed.  This includes the unique
        ID of the bean (see :meth:`get_insert_row`).

        """
        return tuple(map(lambda x: getattr(self, x), self.get_attr_names()))

    def get_insert_row(self) -> Tuple[Any]:
        """Return a row of data meant to be inserted into the database.  This
        method implementation leaves off the first attriubte assuming it
        contains a unique (i.e. row ID) of the object.  See :meth:`get_row`.

        """
        names = self.get_attr_names()
        return tuple(map(lambda x: getattr(self, x), names[1:]))

    def __eq__(self, other):
        if other is None:
            return False
        if self is other:
            return True
        if self.__class__ != other.__class__:
            return False
        for n in self.get_attr_names():
            if getattr(self, n) != getattr(other, n):
                return False
        return True

    def __hash__(self):
        vals = tuple(map(lambda n: getattr(self, n), self.get_attr_names()))
        return hash(vals)

    def __str__(self):
        return ', '.join(map(lambda x: f'{x}: {getattr(self, x)}',
                             self.get_attr_names()))

    def __repr__(self):
        return self.__str__()


@dataclass
class ReadOnlyBeanDbPersister(DbPersister):
    """A read-only persister that CRUDs data based on predefined SQL given in
    the configuration.  The class optionally works with instances of
    :class:`.Bean` when :obj:`row_factory` is set to the target bean class.

    """
    select_name: str = field(default=None)
    """The name of the SQL entry used to select data/class."""

    select_by_id_name: str = field(default=None)
    """The name of the SQL entry used to select a single row by unique ID."""

    select_exists_name: str = field(default=None)
    """The name of the SQL entry used to determine if a row exists by unique
    ID.

    """

    def get(self) -> list:
        """Return using the SQL provided by the entry identified by
        :obj:`select_name`.

        """
        return self.execute_by_name(
            self.select_name, row_factory=self.row_factory)

    def get_by_id(self, id: int):
        """Return an object using it's unique ID, which is could be the row ID
        in SQLite.

        """
        rows = self.execute_by_name(
            self.select_by_id_name, params=(id,), row_factory=self.row_factory)
        if len(rows) > 0:
            return rows[0]

    def exists(self, id: int) -> bool:
        """Return ``True`` if there is a object with unique ID (or row ID) in
        the database.  Otherwise return ``False``.

        """
        if self.select_exists_name is None:
            return self.get_by_id(id) is not None
        else:
            cnt = self.execute_by_name(
                self.select_exists_name, params=(id,), row_factory='tuple')
            return cnt[0][0] == 1


@dataclass
class InsertableBeanDbPersister(ReadOnlyBeanDbPersister):
    """A class that contains insert funtionality.

    """
    insert_name: str = field(default=None)
    """The name of the SQL entry used to insert data/class instance."""

    def insert_row(self, *row) -> int:
        """Insert a row in the database and return the current row ID.

        :param row: a sequence of data in column order of the SQL provided by
                    the entry :obj:`insert_name`

        """
        return self.execute_no_read(self.insert_name, params=row)

    @connection()
    def insert_rows(self, conn: Any, rows: Iterable[Any], errors: str = 'raise',
                    set_id_fn: Callable = None, map_fn: Callable = None) -> int:
        """Insert a tuple of rows in the database and return the current row ID.

        :param rows: a sequence of tuples of data (or an object to be
                     transformed, see ``map_fn`` in column order of the SQL
                     provided by the entry :obj:`insert_name`

        :param errors: if this is the string ``raise`` then raise an error on
                       any exception when invoking the database execute

        :param set_id_fn: a callable that is given the data to be inserted and
                          the row ID returned from the row insert as parameters

        :param map_fn: if not ``None``, used to transform the given row in to a
                       tuple that is used for the insertion

        :return: the ``rowid`` of the last row inserted

        """
        entry_name = self.insert_name
        self._check_entry(entry_name)
        sql = self.sql_entries[entry_name]
        return self.conn_manager.insert_rows(
            conn, sql, rows, errors, set_id_fn, map_fn)

    @connection()
    def insert_dataframe(self, conn: Any, df: pd.DataFrame,
                         errors: str = 'raise', set_id_fn: Callable = None,
                         map_fn: Callable = None, chunk_size: int = 100) -> int:
        """Like :meth:`insert_rows` but the data is taken a Pandas dataframe.

        :param df: the dataframe from which the rows are drawn

        :param set_id_fn: a callable that is given the data to be inserted and
                          the row ID returned from the row insert as parameters

        :param map_fn: if not ``None``, used to transform the given row in to a
                       tuple that is used for the insertion

        :param chuck_size: the number of rows inserted at a time, so the number
                           of interactions with the database are at most the row
                           count of the dataframe / ``chunk_size``x

        :return: the ``rowid`` of the last row inserted

        """
        entry_name: str = self.insert_name
        sql: str = self._get_entry(entry_name)
        row_id: int
        rows: List[Tuple[Any, ...]]
        for rows in chunks(df.itertuples(name=None, index=False), chunk_size):
            row_id = self.conn_manager.insert_rows(
                conn, sql, rows, errors, set_id_fn, map_fn)
        return row_id

    def _get_insert_row(self, bean: Bean) -> Tuple[Any]:
        """Factory method to return the bean's insert row parameters."""
        return bean.get_insert_row()

    def insert(self, bean: Bean) -> int:
        """Insert a bean using the order of the values given in
        :meth:`Bean.get_insert_row` as that of the SQL defined with entry
        :obj:`insert_name` given in the initializer.

        """
        row = self._get_insert_row(bean)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'inserting row: {row}')
        curid = self.insert_row(*row)
        bean.id = curid
        return curid

    def insert_beans(self, beans: Iterable[Any], errors: str = 'raise') -> int:
        """Insert a bean using the order of the values given in
        :meth:`Bean.get_insert_row` as that of the SQL defined with entry
        :obj:`insert_name` given in the initializer.

        """
        def map_fn(bean):
            return self._get_insert_row(bean)

        def set_id_fn(bean, id):
            pass

        return self.insert_rows(beans, errors, set_id_fn, map_fn)


@dataclass
class UpdatableBeanDbPersister(InsertableBeanDbPersister):
    """A class that contains the remaining CRUD funtionality the super class
    doesn't have.

    """
    update_name: str = field(default=None)
    """The name of the SQL entry used to update data/class instance(s)."""

    delete_name: str = field(default=None)
    """The name of the SQL entry used to delete data/class instance(s)."""

    def update_row(self, *row: Tuple[Any]) -> int:
        """Update a row using the values of the row with the current unique ID
        as the first element in ``*rows``.

        """
        where_row = (*row[1:], row[0])
        return self.execute_no_read(self.update_name, params=where_row)

    def update(self, bean: Bean) -> int:
        """Update a a bean that using the ``id`` attribute and its attributes as
        values.

        """
        return self.update_row(*bean.get_row())

    def delete(self, id) -> int:
        """Delete a row by ID.

        """
        return self.execute_no_read(self.delete_name, params=(id,))


@dataclass
class BeanDbPersister(UpdatableBeanDbPersister):
    """A class that contains the remaining CRUD funtionality the super class
    doesn't have.

    """
    keys_name: str = field(default=None)
    """The name of the SQL entry used to fetch all keys."""

    count_name: str = field(default=None)
    """The name of the SQL entry used to get a row count."""

    def get_keys(self) -> Iterable[Any]:
        """Return the unique keys from the bean table.

        """
        keys = self.execute_by_name(self.keys_name, row_factory='tuple')
        return map(lambda x: x[0], keys)

    def get_count(self) -> int:
        """Return the number of rows in the bean table.

        """
        if self.count_name is not None:
            cnt = self.execute_by_name(self.count_name, row_factory='tuple')
            return cnt[0][0]
        else:
            # SQLite has a bug that returns one row with all null values
            return sum(1 for _ in self.get_keys())
