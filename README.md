# tox-gh

[![PyPI version](https://badge.fury.io/py/tox-gh.svg)](https://badge.fury.io/py/tox-gh)
[![PyPI Supported Python Versions](https://img.shields.io/pypi/pyversions/tox-gh.svg)](https://pypi.python.org/pypi/tox-gh/)
[![check](https://github.com/tox-dev/tox-gh/actions/workflows/check.yml/badge.svg)](https://github.com/tox-dev/tox-gh/actions/workflows/check.yml)

**tox-gh** is a tox plugin which helps running tox on GitHub Actions with multiple different Python versions on multiple
workers in parallel.

## Features

When running tox on GitHub Actions, tox-gh

- detects which environment to run based on configurations and
- provides utilities such as
  [grouping log lines](https://github.com/actions/toolkit/blob/main/docs/commands.md#group-and-ungroup-log-lines).

## Usage

1. Add configurations under `[gh]` section along with your tox configuration.
2. Install `tox-gh` package in the GitHub Actions workflow before running `tox` command.

## Examples

### Basic Example

Add `[gh]` section to the same file as tox configuration. If you're using `tox.ini`:

```ini
[gh]
python =
    3.12 = py312
    3.11 = py311, type
    3.10 = py310
    3.9 = py39
    3.8 = py38
    3.7 = py37
```

This will run different set of tox environments on different python versions set up via GitHub `setup-python` action:

- on Python 3.7 job, tox runs `py37` environment,
- on Python 3.8 job, tox runs `py38` environment,
- on Python 3.9 job, tox runs `py39` environment,
- on Python 3.10 job, tox runs `py310` environment,
- in Python 3.11 job, tox runs `py311` and `type` environments,
- on Python 3.12 job, tox runs `py312` environment.

#### Workflow Configuration

`.github/workflows/check.yml`:

```yaml
name: check
on:
  push:
  pull_request:
  schedule:
    - cron: "0 8 * * *"

concurrency:
  group: check-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    name: test with ${{ matrix.py }} on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        py:
          - "3.12"
          - "3.11"
          - "3.10"
          - "3.9"
          - "3.8"
          - "3.7"
        os:
          - ubuntu-latest
          - macos-latest
          - windows-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      - name: Setup python for test ${{ matrix.py }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.py }}
      - name: Install tox
        run: python -m pip install tox-gh>=1.2
      - name: Setup test suite
        run: tox -vv --notest
      - name: Run test suite
        run: tox --skip-pkg-install
```

## FAQ

- When a list of environments to run is specified explicitly via `-e` option or `TOXENV` environment variable `tox-gh`
  respects the given environments and simply runs the given environments without enforcing its configuration.
- The plugin only activates if the environment variable `GITHUB_ACTIONS` is `true`.
