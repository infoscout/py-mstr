# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.1.0] - 2020-05-28

### Added
- Python 2 support.

## [1.0.0] - 2020-04-28

### Added
- Python 3 support.

### Removed
- Python 2 support.

## [0.2.2] - 2018-10-01

### Added
- Add timeout support for report `execute` method

### Changed
- Upgraded CircleCI to 2.0
- Switched resource_class on CircleCI from medium (default) to small

## [0.2.1] - 2018-02-19

### Added
- FIX: Raise `MstrClientException` if the MicroStrategy server returns an error response
- Created common `MstrTestCase` base class to handle common `setUp`/`tearDown` operations

### Changed
- Switched from mox library to mock library

### Removed
- Deleted empty test cases

## [0.2.0] - 2017-12-08

### Added
- Miscellaneous repo quality improvements:
  - Added monitoring of code coverage using CodeCov
  - Fixed various linting errors
  - Added more classifiers to `setup.py`

### Changed
- FIX: Updated `install_requires` to require `pyquery` < 1.3.0 since 1.3.0 is not compatible with `py-mstr`
- FIX: Updated `maxCols` in tests to reflect update in 0.1.1

### Removed
- Dropped Python 2.6 support

## [0.1.1] - 2015-07-27

### Changed
- Increased report execute `max_cols` from 10 to 255
- Loosened `install_requires` to allow newer versions of `pyquery` and `requests`

## [0.1.0] - 2014-07-31

### Added
- Ability to connect to MicroStrategy Web Task API
  - Most critical methods available through the API have been implemented, including the ability to execute a report with or without prompts
- Initial tests
- Initial documentation
