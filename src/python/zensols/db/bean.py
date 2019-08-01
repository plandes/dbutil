"""Basic CRUD utility classes

"""
__author__ = 'Paul Landes'

import logging
from pathlib import Path
from abc import abstractmethod, ABC
from zensols.actioncli import (
    resource,
    Stash,
)
from zensols.db import DynamicDataParser

logger = logging.getLogger(__name__)


class connection(resource):
    """Annotation used to create and dispose of DB-API connections.

    """
    def __init__(self):
        super(connection, self).__init__(
            '_create_connection', '_dispose_connection')


class ConnectionFactory(ABC):
    """Instance DB-API connection lifecycle.

    """
    @abstractmethod
    def create(self):
        """Create a connection to the database.

        """
        pass

    def dispose(self, conn):
        """Close the connection to the database.

        """
        conn.close()


class DbPersister(object):
    """CRUDs data to/from a DB-API connection.

    """
    def __init__(self, sql_file: Path, conn_factory: ConnectionFactory):
        """Initialize.

        :param sql_file: the text file containing the SQL statements (see
                         ``DynamicDataParser``)
        :param conn_factory: used to create DB-API connections

        """
        self.parser = DynamicDataParser(sql_file)
        self.conn_factory = conn_factory

    @property
    def sql_entries(self) -> dict:
        """Return a dictionary of names -> SQL statements.

        """
        return self.parser.sections

    def _create_connection(self):
        """Create a connection to the database.

        """
        logger.debug(f'creating connection')
        return self.conn_factory.create()

    def _dispose_connection(self, conn):
        """Close the connection to the database.

        :param conn: the connection to release

        """
        logger.debug(f'closing connection {conn}')
        self.conn_factory.dispose(conn)

    @staticmethod
    def _dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def _check_entry(self, name):
        if name is None:
            raise ValueError(f'no defined SQL entry for persist function')
        if len(name) == 0:
            raise ValueError(f"non-optional entry not provided")
        if name not in self.sql_entries:
            raise ValueError(f"no entry '{name}' found in SQL configuration")

    @connection()
    def execute(self, conn, sql, params=(), row_factory='tuple', map_fn=None):
        """Execute SQL on a database connection.

        :param conn: the connection object with the database
        :param sql: the string SQL to execute
        :param params: the parameters given to the SQL statement (populated
                       with ``?``) in the statement
        :param row_factory: informs how to create result sets; ``dict`` for
                            dictionaries, ``tuple`` for tuples otherwise a
                            function or class (default to tuples)

        """
        def second(cursor, row):
            return cls(*row)

        rfs = {'dict': self._dict_factory,
               'tuple': None}
        if row_factory in rfs:
            row_factory = rfs[row_factory]
        else:
            cls = row_factory
            row_factory = second
        if row_factory is not None:
            conn.row_factory = row_factory
        cur = conn.cursor()
        try:
            res = cur.execute(sql, params)
            if map_fn is not None:
                res = map(map_fn, res)
            return tuple(res)
        finally:
            cur.close()

    def execute_by_name(self, name, params=(), row_factory='tuple',
                        map_fn=None):
        """Just like ``execute`` but look up the SQL.

        :param name: the name of the SQL entry used for the query
        :param sql: the string SQL to execute
        :param params: the parameters given to the SQL statement (populated
                       with ``?``) in the statement
        :param row_factory: informs how to create result sets; ``dict`` for
                            dictionaries, ``tuple`` for tuples otherwise a
                            function or class (default to tuples)
        """
        self._check_entry(name)
        sql = self.sql_entries[name]
        return self.execute(sql, params, row_factory, map_fn)

    def execute_singleton_by_name(self, *args, **kwargs):
        """Just like ``execute_by_name`` except return only the first item or ``None``
        if no results.

        """
        res = self.execute_by_name(*args, **kwargs)
        if len(res) > 0:
            return res[0]

    def execute_no_read(self, conn, entry_name, params=()) -> int:
        """Execute SQL returning the last row ID from the cursor.

        """
        self._check_entry(entry_name)
        sql = self.sql_entries[entry_name]
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid


class Bean(ABC):
    """A container class like a Java *bean*.

    """
    @abstractmethod
    def get_attr_names(self) -> list:
        """Return a list of string attribute names.

        """
        pass

    def get_attrs(self) -> dict:
        """Return a dict of attributes that are meant to be persisted.
        """
        return {n: getattr(self, n) for n in self.get_attr_names()}

    def get_row(self) -> tuple:
        """Return a row of data meant to be printed.  This includes the unique ID of
        the bean (see ``get_insert_row``).

        """
        return tuple(map(lambda x: getattr(self, x), self.get_attr_names()))

    def get_insert_row(self) ->tuple:
        """Return a row of data meant to be inserted into the database.  This method
        implementation leaves off the first attriubte assuming it contains a
        unique (i.e. row ID) of the object.  See ``get_row``.

        """
        names = self.get_attr_names()
        return tuple(map(lambda x: getattr(self, x), names[1:]))

    def __str__(self):
        return ', '.join(map(lambda x: f'{x}: {getattr(self, x)}',
                             self.get_attr_names()))

    def __repr__(self):
        return self.__str__()


class ReadOnlyBeanDbPersister(DbPersister):
    """A read-only persister that CRUDs data based on predefined SQL given in the
    configuration.  The class optionally works with instances of ``Bean`` when
    ``row_factory`` is set to the target bean class.

    """
    def __init__(self, *args, select_name: str = None, select_by_id: str = None,
                 select_exists: str = None, row_factory='tuple', **kwargs):
        """Initialize.

        :param select_name: the name of the SQL entry used to select data/class
        :param row_factory: the row_factory parameter in ``get_all``
                            when none is givne (see class docs)

        """
        super(ReadOnlyBeanDbPersister, self).__init__(*args, **kwargs)
        self.select_name = select_name
        self.select_by_id = select_by_id
        self.select_exists = select_exists
        self.row_factory = row_factory

    def get(self) -> list:
        """Return using the SQL provided by the entry ``select_name``.

        """
        return self.execute_by_name(
            self.select_name, row_factory=self.row_factory)

    def get_by_id(self, id: int):
        """Return an object using it's unique ID, which is could be the row ID in
        SQLite.

        """
        rows = self.execute_by_name(
            self.select_by_id, params=(id,), row_factory=self.row_factory)
        if len(rows) > 0:
            return rows[0]

    def exists(self, id: int) -> bool:
        """Return ``True`` if there is a object with unique ID (or row ID) in the
        database.  Otherwise return ``False``.

        """
        if self.select_exists is None:
            return self.get_by_id(id) is not None
        else:
            cnt = self.execute_by_name(
                self.select_exists, params=(id,), row_factory='tuple')
            return cnt[0][0] == 1


class InsertableBeanDbPersister(ReadOnlyBeanDbPersister):
    """A class that contains insert funtionality.

    """
    def __init__(self, *args, insert_name: str = None, **kwargs):
        """Initialize.

        :param insert_name: the name of the SQL entry used to insert data/class
                            instance

        """
        super(InsertableBeanDbPersister, self).__init__(*args, **kwargs)
        self.insert_name = insert_name

    @connection()
    def insert_row(self, conn, *row) -> int:
        """Insert a row in the database and return the current row ID.

        :param row: a sequence of data in column order of the SQL provided by
                    the entry ``insert_name``

        """
        return self.execute_no_read(conn, self.insert_name, params=row)

    @connection()
    def insert_rows(self, conn, rows, errors='raise') -> int:
        """Insert a tuple of rows in the database and return the current row ID.

        :param row: a sequence of tuples of data in column order of the SQL
                    provided by the entry ``insert_name``

        """
        entry_name = self.insert_name
        self._check_entry(entry_name)
        sql = self.sql_entries[entry_name]
        cur = conn.cursor()
        for row in rows:
            if errors == 'raise':
                cur.execute(sql, row)
            elif errors == 'ignore':
                try:
                    cur.execute(sql, row)
                except Exception as e:
                    logger.error(f'could not insert row ({len(row)})', e)
            else:
                raise ValueError(f'unknown errors value: {errors}')
        conn.commit()
        return cur.lastrowid

    def insert(self, bean: Bean) -> int:
        """Insert a bean using the order of the values given in ``get_insert_row`` as
        that of the SQL defined with entry ``insert_name`` given in the
        initializer.

        """
        curid = self.insert_row(*bean.get_insert_row())
        bean.id = curid
        return curid

    def insert_beans(self, beans: list) -> int:
        """Insert a bean using the order of the values given in ``get_insert_row`` as
        that of the SQL defined with entry ``insert_name`` given in the
        initializer.

        """
        curid = None
        for bean in beans:
            curid = self.insert(bean)
        return curid


class UpdatableBeanDbPersister(InsertableBeanDbPersister):
    """A class that contains the remaining CRUD funtionality the super class
    doesn't have.

    """
    def __init__(self, *args, update_name: str = None, delete_name: str = None,
                 **kwargs):
        """Initialize.

        :param update_name: the name of the SQL entry used to update data/class
                            instance

        """
        super(UpdatableBeanDbPersister, self).__init__(*args, **kwargs)
        self.update_name = update_name
        self.delete_name = delete_name

    @connection()
    def update_row(self, conn, *row) -> int:
        """Update a row using the values of the row with the current unique ID as the
        first element in ``*rows``.

        """
        where_row = (*row[1:], row[0])
        return self.execute_no_read(conn, self.update_name, params=where_row)

    def update(self, bean: Bean) -> int:
        """Update a a bean that using the ``id`` attribute and its attributes as
        values.

        """
        return self.update_row(*bean.get_row())

    @connection()
    def delete(self, conn, id) -> int:
        """Delete a row by ID.

        """
        return self.execute_no_read(conn, self.delete_name, params=(id,))


class BeanDbPersister(UpdatableBeanDbPersister):
    """A class that contains the remaining CRUD funtionality the super class
    doesn't have.

    """
    def __init__(self, *args, keys_name: str = None, count_name: str = None,
                 **kwargs):
        """Initialize.

        :param update_name: the name of the SQL entry used to update data/class
                            instance

        """
        super(BeanDbPersister, self).__init__(*args, **kwargs)
        self.keys_name = keys_name
        self.count_name = count_name

    def get_keys(self) -> list:
        """Delete a row by ID.

        """
        keys = self.execute_by_name(self.keys_name)
        return map(lambda x: x[0], keys)

    def get_count(self) -> int:
        """Return the number of rows in the bean table.

        """
        if self.count_name is not None:
            cnt = self.execute_by_name(self.count_name)
            return cnt[0][0]
        else:
            # SQLite has a bug that returns one row with all null values
            return sum(1 for _ in self.get_keys())


class BeanStash(Stash):
    """A stash that uses a backing DB-API backed ``BeanDbPersister``.

    """
    def __init__(self, persister: BeanDbPersister):
        self.persister = persister

    def load(self, name: str):
        return self.persister.get_by_id(int(name))

    def exists(self, name: str):
        return self.persister.exists(int(name))

    def dump(self, name: str, inst):
        """Since this implementation can let the database auto-increment the
        unique/primary key, beware of "changing" keys.  If the key changes
        after inserted it will raise a ``ValueError``.  For this reason, it's
        best to pass ``None`` as ``name``.

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
            raise ValueError(f'unexpected key change: {inst.id} != {id}')
        return inst

    def delete(self, name):
        self.persister.delete(name)

    def keys(self):
        return self.persister.get_keys()

    def __len__(self):
        return self.persister.get_count()
