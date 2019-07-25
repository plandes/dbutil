# Database convenience utilities.

[![Travis CI Build Status][travis-badge]][travis-link]
[![PyPI][pypi-badge]][pypi-link]

A library of database convenience utilities, typically for creation of
temporary files for processing large data.

Features:
* DB-API Interface allows combined SQL rapid prototyping with backing
  programmatic usage.
* Java Beans like persistence.
* Integration with [zensols.actioncli stash].
* [SQLite] integration.


## Obtaining

The easist way to install the command line program is via the `pip` installer:
```bash
pip3 install zensols.db
```

Binaries are also available on [pypi].


## Usage

See the [use cases](dbutil/test/python/test_sqlite.py) for examples of how to
use the API.


## Changelog

An extensive changelog is available [here](CHANGELOG.md).


## License

Copyright (c) 2019 Paul Landes

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


<!-- links -->
[travis-link]: https://travis-ci.org/plandes/dbutil
[travis-badge]: https://travis-ci.org/plandes/dbutil.svg?branch=master
[pypi]: https://pypi.org/project/zensols.db/
[pypi-link]: https://pypi.python.org/pypi/zensols.db
[pypi-badge]: https://img.shields.io/pypi/v/zensols.db.svg

[zensols.actioncli stash]: https://github.com/plandes/actioncli/blob/master/src/python/zensols/actioncli/persist.py#L283
[SQLite]: https://www.sqlite.org/index.html
