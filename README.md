# Database convenience utilities.

[![PyPI][pypi-badge]][pypi-link]
[![Python 3.11][python311-badge]][python311-link]
[![Python 3.12][python312-badge]][python312-link]
[![Build Status][build-badge]][build-link]

A library of database convenience utilities, typically for creation of
temporary files for processing large data.

Features:
* DB-API Interface allows combined SQL rapid prototyping with backing
programmatic usage.
* Java Beans like persistence.
* Integration with [zensols.util stash].
* [SQLite] integration.
* [PostgreSQL] integration with the [dbutilpg] library.
* [Pandas] data frame creation, which is agnostic of database provider.


## Documentation

See the [full documentation](https://plandes.github.io/dbutil/index.html).
The [API reference](https://plandes.github.io/dbutil/api.html) is also
available.


## Obtaining

The easist way to install the command line program is via the `pip` installer:
```bash
pip3 install zensols.db
```

Binaries are also available on [pypi].


## Usage

A simple example is detailed below, and also found in the [repo](example).


### SQL binding file

First, create the SQL file, which is used to create and access the database.
Here we can replace `name, age` with `${cols}` and call it `person.sql`:

```sql
-- meta=init_sections=create_tables,create_idx

-- name=create_idx
create index person_name on person(name);

-- name=create_tables
create table person (name text, age int);

-- name=insert_person
insert into person (${cols}) values (?, ?);

-- name=select_people; note that the order is needed for the unit tests only
select ${cols}, rowid as id
       from person
       order by name;

-- name=select_people_by_id
select ${cols}, rowid as id from person where id = ?;

-- name=update_person
update person set name = ?, age = ? where rowid = ?;

-- name=delete_person
delete from person where rowid = ?;
```

### Persister

Next, create the application context with a persister that is the SQL to client
binding and call it `app.conf`:

```ini
# command line interaction
[cli]
class_name = zensols.cli.ActionCliManager
apps = list: app

# the connection manager, which is the DB binding and in our case SQLite
[sqlite_conn_manager]
class_name = zensols.db.sqlite.SqliteConnectionManager
db_file = path: person.db

# the persister binds the API to the SQL
[person_persister]
class_name = zensols.db.dataclass.DataClassDbPersister
bean_class = class: app.Person
sql_file = person.sql
conn_manager = instance: sqlite_conn_manager
insert_name = insert_person
select_name = select_people
select_by_id = select_people_by_id
update_name = update_person
delete_name = delete_person

# the application class invoked by the CLI
[app]
class_name = app.Application
persister = instance: person_persister
```


### Application

Define the *bean*, which provides the metadata for the `${cols}` in
`person.sql` and can (but not must) be used with the API to CRUD rows:

```python
from dataclasses import dataclass, field
from zensols.db import BeanDbPersister


@dataclass
class Person(object):
    name: str = field()
    age: int = field()
    id: int = field(default=None)


@dataclass
class Application(object):
    """A people database"""

    persister: BeanDbPersister

    def demo(self):
        # create a row using an instance of a dataclass and return the unique
        # ID of the inserted row
        paul_id: int = self.persister.insert(Person('Paul', 31))

        # we can also insert by columns in the order given in the dataclass
        jane_id: int = self.persister.insert_row('Jane', 32)

        # print everyone in the database
        print(self.persister.get())

        # delete a row
        self.persister.delete(paul_id)
        print(self.persister.get())

        # update jane's age
        self.persister.update_row(jane_id, 'jane', 36)

        # get the updated row we just set
        jane = self.persister.get_by_id(jane_id)
        print(f'jane: {jane}')

        # clean up, which for SQLite deletes the file
        self.persister.conn_manager.drop()
```

Create the entry point used on the command line and call it `run.py`:

```python
from zensols.cli import CliHarness

CliHarness(app_config_resource='app.conf').run()
```


### Run

```bash
$ ./run.py -h
Usage: run.py [options]:

A people database.

Options:
  -h, --help      show this help message and exit
  --version       show the program version and exit

$ ./run.py
(Person(name='Jane', age=32, id=2), Person(name='Paul', age=31, id=1))
(Person(name='Jane', age=32, id=2),)
jane: Person(name='jane', age=36, id=2)
```

See the [use cases](test/python/test_sqlite.py) for more detailed examples of
how to use the API.


## Changelog

An extensive changelog is available [here](CHANGELOG.md).


## Community

Please star this repository and let me know how and where you use this API.
Contributions as pull requests, feedback and any input is welcome.


## License

[MIT License](LICENSE.md)

Copyright (c) 2020 - 2025 Paul Landes


<!-- links -->
[pypi]: https://pypi.org/project/zensols.db/
[pypi-link]: https://pypi.python.org/pypi/zensols.db
[pypi-badge]: https://img.shields.io/pypi/v/zensols.db.svg
[python311-badge]: https://img.shields.io/badge/python-3.11-blue.svg
[python311-link]: https://www.python.org/downloads/release/python-3110
[python312-badge]: https://img.shields.io/badge/python-3.12-blue.svg
[python312-link]: https://www.python.org/downloads/release/python-3120
[build-badge]: https://github.com/plandes/dbutil/workflows/CI/badge.svg
[build-link]: https://github.com/plandes/dbutil/actions

[zensols.util stash]: https://github.com/plandes/util/blob/master/src/python/zensols/util/persist.py
[SQLite]: https://www.sqlite.org/index.html

[PostgreSQL]: https://www.postgresql.org
[dbutilpg]: https://github.com/plandes/dbutilpg
[Pandas]: https://pandas.pydata.org
