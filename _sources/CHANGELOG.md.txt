# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## [Unreleased]


## [1.4.0] - 2025-01-11
### Removed
- Support for Python 3.10.

### Changed
- Upgraded to [zensols.util] version 1.15.


## [1.3.2] - 2024-09-18
### Changes
- Refactored `ConnectionManager`, `connection` and other domain classes to
  module `conn`.  This is a low risk refactoring since the new module was added
  to the parent module imports.

### Added
- Connection pooling with class `zensols.db.connpool.PooledConnectionManager`.


## [1.3.1] - 2024-03-14
### Changes
- Bug fix in `DbStash` that robustly handles missing results.


## [1.3.0] - 2024-01-04
### Removed
- Packages `zensols.db.dataclass`, and `zensols.db.dataclass` are no longer
  automatically imported.  You must now import these with their full module
  name to use them.

### Added
- A `zensols.persist.Stash` SQLite implementation that needs no `DbPersister`.
  It uses a unique primary key for stash keys and stores as either a string or
  binary blob for the values.


## [1.2.0] - 2023-12-05
### Changed
- Upgrade to [zensols.util] version 1.14.

### Added
- Support for Python 3.11.

### Removed
- Support for Python 3.9.


## [1.1.0] - 2023-08-16
Functional and downstream moderate risk update release.

### Added
- Cursor iteration.

### Changed
- Renamed `DynamicDataParser.meta` -> `DynamicDataParser.metadata`
- `BeanStash` always uses string keys per contract.
- Simplify `ConnectionManager.execute` treatment of the `row_factory`
  parameter.


## [1.0.0] - 2023-02-02
### Changed
- Rename add `_name` to `select_by_id` and `select_exists` to confirm with
  other selection attributes in `DbPersister`.
- Updated [zensols.util] to 1.12.0.


## [0.2.0] - 2022-10-01
### Added
- Identity row factory.

### Removed
- Python 3.7 and 3.8 support.


## [0.0.12] - 2021-11-30
### Added
- Data classes are supported and need not inherit from `Bean`.
- More documentation and examples.


## [0.0.11] - 2021-03-10
### Changed
- Fixed doc.


## [0.0.10] - 2021-03-10
### Changed
- Switch to new `DBError` in place of generic error.
- Inline `dataclass` field documentation.
- More utilization of `row_factory` in `DbPersister` over `tuple`.  More get
  methods now require explicit tuple request when class level `row_factory` is
  set.
### Added
- Factory methods and type hints for DDL/DML SQL parsing.
- Utility classes to persist `dataclasses.dataclass` instances.


## [0.0.9] - 2021-01-12
### Added
- [Pandas] data frame read access in `DbPersister`.
- API Documentation.
### Changed
- Switch to GitHub workflows.


## [0.0.8] - 2020-12-09
### Added
- Sphinx documentation, which includes API docs.


## [0.0.7] - 2020-12-09
### Changed
- Convert bean and connection manager to data classes.

- Fixed test cases.


## [0.0.6] - 2020-05-05
### Changed
- Remove `ConnectionManagerConfigurer` as a part of upgrading to `zensol.util`
  per v. 1.2.3.


## [0.0.5] - 2020-04-25
### Changed
- Upgrade to ``zensols.util`` 1.2.0.
### Removed
- Drop Python 3.6 support.


## [0.0.4] - 2019-09-28
### Changed
- Better clear/delete functionality.
- Bug fixes.


## [0.0.3] - 2019-08-07
### Changed
- Refactor and clean up to allow for PostreSQL extension.


## [0.0.2] - 2019-07-31
### Changed
- More efficient bean insertion.
- Better resource clean up.


## [0.0.1] - 2019-07-21
### Added
- Initial version.


<!-- links -->
[Unreleased]: https://github.com/plandes/dbutil/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/plandes/dbutil/compare/v1.3.2...v1.4.0
[1.3.2]: https://github.com/plandes/dbutil/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/plandes/dbutil/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/plandes/dbutil/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/plandes/dbutil/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/plandes/dbutil/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/plandes/dbutil/compare/v0.2.0...v1.0.0
[0.2.0]: https://github.com/plandes/dbutil/compare/v0.0.12...v0.2.0
[0.0.12]: https://github.com/plandes/dbutil/compare/v0.0.11...v0.0.12
[0.0.11]: https://github.com/plandes/dbutil/compare/v0.0.10...v0.0.11
[0.0.10]: https://github.com/plandes/dbutil/compare/v0.0.9...v0.0.10
[0.0.9]: https://github.com/plandes/dbutil/compare/v0.0.8...v0.0.9
[0.0.8]: https://github.com/plandes/dbutil/compare/v0.0.7...v0.0.8
[0.0.7]: https://github.com/plandes/dbutil/compare/v0.0.6...v0.0.7
[0.0.6]: https://github.com/plandes/dbutil/compare/v0.0.5...v0.0.6
[0.0.5]: https://github.com/plandes/dbutil/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/plandes/dbutil/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/plandes/dbutil/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/plandes/dbutil/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/plandes/dbutil/compare/v0.0.0...v0.0.1


[Pandas]: https://pandas.pydata.org
[zensols.util]: https://github.com/plandes/util
