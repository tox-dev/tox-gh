# tox-gh

[![PyPI version](https://badge.fury.io/py/tox-gh.svg)](https://badge.fury.io/py/tox-gh)
[![PyPI Supported Python Versions](https://img.shields.io/pypi/pyversions/tox-gh.svg)](https://pypi.python.org/pypi/tox-gh/)
[![check](https://github.com/tox-dev/tox-gh/actions/workflows/check.yaml/badge.svg)](https://github.com/tox-dev/tox-gh/actions/workflows/check.yaml)
[![Downloads](https://static.pepy.tech/badge/tox-gh/month)](https://pepy.tech/project/tox-gh)

**tox-gh** is a tox plugin, which helps run tox on GitHub Actions with multiple different Python versions on multiple
workers in parallel.

## Features

When running tox on GitHub Actions, tox-gh:

- detects which environment to run based on configurations (or bypasses detection and sets it explicitly via the
  `TOX_GH_MAJOR_MINOR` environment variable),
- provides utilities such as
  [grouping log lines](https://github.com/actions/toolkit/blob/main/docs/commands.md#group-and-ungroup-log-lines).

## Usage

1. Add configurations under `[gh]` section along with your tox configuration.
2. Install `tox-gh` package in the GitHub Actions workflow before running `tox` command.

## Examples

### Basic Example

Add `[gh]` section to the same file as tox configuration.

If you're using `tox.ini`:

```ini
[gh]
python =
    3.14t = 3.14t
    3.14 = 3.14, type, dev, pkg_meta
    3.13 = 3.13
    3.12 = 3.12
```

For `tox.toml`:

```toml
[gh.python]
"3.14t" = ["3.14t",]
"3.14" = ["3.14", "type", "pkg_meta"]
"3.13" = ["3.13"]
"3.12" = ["3.12"]
```

For `pyproject.toml`:

```toml
[tool.tox.gh.python]
"3.14t" = ["3.14t"]
"3.14" = ["3.14", "type", "pkg_meta"]
"3.13" = ["3.13"]
"3.12" = ["3.12"]
```

This will run a different set of tox environments on different Python versions set up via GitHub `setup-python` action:

- on Python 3.14t job, tox runs `3.14t` environment,
- on Python 3.14 job, tox runs `3.14`, `type` and `pkg_meta` environments,
- on Python 3.13 job, tox runs `3.13` environment,
- on Python 3.12 job, tox runs `3.12` environment,

#### Workflow Configuration

A bare-bones example would be `.github/workflows/check.yaml`:

```yaml
jobs:
  test:
    name: test with ${{ matrix.env }} on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        env:
          - "3.14t"
          - "3.14"
          - "3.13"
        os:
          - ubuntu-latest
          - macos-latest
    steps:
      - uses: actions/checkout@v5
      - name: Install the latest version of uv
        uses: astral-sh/setup-uv@v7
      - name: Install tox
        run: uv tool install --python-preference only-managed --python 3.14 tox --with tox-uv --with tox-gh
      - name: Install Python
        if: matrix.env != '3.14'
        run: uv python install --python-preference only-managed ${{ matrix.env }}
      - name: Setup test suite
        run: tox run -vv --notest --skip-missing-interpreters false
        env:
          TOX_GH_MAJOR_MINOR: ${{ matrix.env }}
      - name: Run test suite
        run: tox run --skip-pkg-install
        env:
          TOX_GH_MAJOR_MINOR: ${{ matrix.env }}
```

A more exhaustive example would be `.github/workflows/check.yaml`:

```yaml
name: check
on:
  workflow_dispatch:
  push:
    branches: ["main"]
    tags-ignore: ["**"]
  pull_request:
  schedule: # Runs at 8 AM every day
    - cron: "0 8 * * *"

concurrency:
  group: check-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    name: test with ${{ matrix.env }} on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        env:
          - "3.14t"
          - "3.14"
          - "3.13"
        os:
          - ubuntu-latest
          - macos-latest
          - windows-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0
      - name: Install the latest version of uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
          cache-dependency-glob: "pyproject.toml"
          github-token: ${{ secrets.GITHUB_TOKEN }}
      - name: Add .local/bin to Windows PATH
        if: runner.os == 'Windows'
        shell: bash
        run: echo "$USERPROFILE/.local/bin" >> $GITHUB_PATH
      - name: Install tox
        run: uv tool install --python-preference only-managed --python 3.14 tox --with tox-uv --with tox-gh
      - name: Install Python
        if: matrix.env != '3.14'
        run: uv python install --python-preference only-managed ${{ matrix.env }}
      - name: Setup test suite
        run: tox run -vv --notest --skip-missing-interpreters false
        env:
          TOX_GH_MAJOR_MINOR: ${{ matrix.env }}
      - name: Run test suite
        run: tox run --skip-pkg-install
        env:
          TOX_GH_MAJOR_MINOR: ${{ matrix.env }}
```

## FAQ

- When a list of environments to run is specified explicitly via `-e` option or `TOXENV` environment variable `tox-gh`
  respects the given environments and simply runs the given environments without enforcing its configuration.
- The plugin only activates if the environment variable `GITHUB_ACTIONS` is `true`.
