# Database convenience utilities.

[![PyPI][pypi-badge]][pypi-link]
[![Python 3.7][python37-badge]][python37-link]
[![Python 3.8][python38-badge]][python38-link]
[![Python 3.9][python39-badge]][python39-link]
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

See the [use cases](test/python/test_sqlite.py) for examples of how to
use the API.


## Changelog

An extensive changelog is available [here](CHANGELOG.md).


## License

[MIT License](LICENSE.md)

Copyright (c) 2020 - 2021 Paul Landes


<!-- links -->
[pypi]: https://pypi.org/project/zensols.db/
[pypi-link]: https://pypi.python.org/pypi/zensols.db
[pypi-badge]: https://img.shields.io/pypi/v/zensols.db.svg
[python37-badge]: https://img.shields.io/badge/python-3.7-blue.svg
[python37-link]: https://www.python.org/downloads/release/python-370
[python38-badge]: https://img.shields.io/badge/python-3.8-blue.svg
[python38-link]: https://www.python.org/downloads/release/python-380
[python39-badge]: https://img.shields.io/badge/python-3.9-blue.svg
[python39-link]: https://www.python.org/downloads/release/python-390
[build-badge]: https://github.com/plandes/dbutil/workflows/CI/badge.svg
[build-link]: https://github.com/plandes/dbutil/actions

[zensols.util stash]: https://github.com/plandes/util/blob/master/src/python/zensols/util/persist.py
[SQLite]: https://www.sqlite.org/index.html

[PostgreSQL]: https://www.postgresql.org
[dbutilpg]: https://github.com/plandes/dbutilpg
[Pandas]: https://pandas.pydata.org
