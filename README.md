# tox-gh

[![PyPI version](https://badge.fury.io/py/tox-gh.svg)](https://badge.fury.io/py/tox-gh)
[![PyPI Supported Python Versions](https://img.shields.io/pypi/pyversions/tox-gh.svg)](https://pypi.python.org/pypi/tox-gh/)
[![check](https://github.com/tox-dev/tox-gh/actions/workflows/check.yaml/badge.svg)](https://github.com/tox-dev/tox-gh/actions/workflows/check.yaml)
[![Downloads](https://static.pepy.tech/badge/tox-gh/month)](https://pepy.tech/project/tox-gh)

Seamless integration of tox into GitHub Actions.

**tox-gh** automatically selects which tox environments to run on each Python version in your GitHub Actions matrix,
allowing parallel test execution across multiple workers.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Tutorial: Getting Started](#tutorial-getting-started)
  - [Prerequisites](#prerequisites)
  - [Step 1: Add tox-gh configuration](#step-1-add-tox-gh-configuration)
  - [Step 2: Create a GitHub Actions workflow](#step-2-create-a-github-actions-workflow)
  - [Step 3: Push and verify](#step-3-push-and-verify)
- [How-to Guides](#how-to-guides)
  - [How to run multiple environments on a single Python version](#how-to-run-multiple-environments-on-a-single-python-version)
  - [How to test freethreaded Python builds](#how-to-test-freethreaded-python-builds)
  - [How to explicitly set the Python version](#how-to-explicitly-set-the-python-version)
  - [How to bypass tox-gh environment selection](#how-to-bypass-tox-gh-environment-selection)
  - [How to use with uv](#how-to-use-with-uv)
- [Reference](#reference)
  - [Configuration](#configuration)
    - [`[gh.python]`](#ghpython)
  - [Environment Variables](#environment-variables)
    - [`GITHUB_ACTIONS`](#github_actions)
    - [`TOX_GH_MAJOR_MINOR`](#tox_gh_major_minor)
    - [`TOXENV`](#toxenv)
  - [Python Version Detection](#python-version-detection)
  - [GitHub Actions Integration](#github-actions-integration)
    - [Log Grouping](#log-grouping)
    - [Step Summary](#step-summary)
  - [Behavior](#behavior)
    - [Activation Conditions](#activation-conditions)
    - [Environment Selection](#environment-selection)
    - [Subprocess Provisioning](#subprocess-provisioning)
- [Explanation](#explanation)
  - [Why tox-gh exists](#why-tox-gh-exists)
  - [How environment selection works](#how-environment-selection-works)
  - [Design decisions](#design-decisions)
  - [Comparison to tox-gh-actions](#comparison-to-tox-gh-actions)
  - [Limitations](#limitations)

<!-- mdformat-toc end -->

______________________________________________________________________

## Tutorial: Getting Started

This guide walks you through setting up tox-gh for the first time.

### Prerequisites

You'll need a Python project already using tox 4 with a `tox.toml`, `tox.ini`, or `pyproject.toml` configuration file.

### Step 1: Add tox-gh configuration

Open your tox configuration file and add a `[gh]` section that maps Python versions to tox environments.

For `tox.toml`:

```toml
[gh.python]
"3.13" = ["py313"]
"3.12" = ["py312"]
```

For `tox.ini`:

```ini
[gh]
python =
    3.13 = py313
    3.12 = py312
```

This tells tox-gh: "When running on Python 3.13, run the `py313` environment. When running on Python 3.12, run the
`py312` environment."

> **Note**: In `tox.ini`, the `[gh] python` dict entries must use `=` as the key-value separator (not `:`). Using `:`
> will cause parsing to fail silently since `:` is an INI key-value delimiter.

### Step 2: Create a GitHub Actions workflow

Create `.github/workflows/test.yaml`:

```yaml
name: test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.13', '3.12']
    steps:
      - uses: actions/checkout@v5
      - name: Install uv
        uses: astral-sh/setup-uv@v7
      - name: Install tox
        run: |
          uv tool install --python ${{ matrix.python-version }} tox --with tox-gh
      - name: Run tests
        run: tox
```

### Step 3: Push and verify

Commit your changes and push to GitHub. The workflow will run automatically. You'll see:

- Two parallel jobs (one for Python 3.13, one for 3.12)
- Each job runs only its corresponding tox environment
- GitHub Actions log groups organize output by environment

You've successfully integrated tox-gh. The plugin now handles environment selection automatically based on which Python
version GitHub Actions provides.

______________________________________________________________________

## How-to Guides

### How to run multiple environments on a single Python version

Add a list of environments for a Python version:

```toml
[gh.python]
"3.13" = ["py313", "type", "lint"]
```

In `tox.ini`:

```ini
[gh]
python =
    3.13 = py313, type, lint
```

Now the Python 3.13 job will run three tox environments sequentially: `py313`, `type`, and `lint`.

When using factored environments (e.g., `py313-django{50,51}`), list the full env names since tox-gh **replaces** the
envlist rather than filtering it:

```toml
[gh.python]
"3.13" = ["py313-django{50,51,52}"]
"3.12" = ["py312-django{50,51,52}"]
```

In `tox.ini`:

```ini
[gh]
python =
    3.13 = py313-django{50,51,52}
    3.12 = py312-django{50,51,52}
```

### How to test freethreaded Python builds

Freethreaded Python (3.13t, 3.14t) is automatically detected. Map it like any other version:

```toml
[gh.python]
"3.14t" = ["py314t"]
"3.14" = ["py314", "type"]
```

In `tox.ini`:

```ini
[gh]
python =
    3.14t = py314t
    3.14 = py314, type
```

The plugin checks for the freethreaded attribute and generates the correct version key with the `t` suffix.

### How to explicitly set the Python version

If automatic detection doesn't work for your setup, set `TOX_GH_MAJOR_MINOR`:

```yaml
  - name: Run tests
    run: tox
    env:
      TOX_GH_MAJOR_MINOR: ${{ matrix.python-version }}
```

This forces tox-gh to use the matrix value instead of detecting the Python version.

### How to bypass tox-gh environment selection

Run tox with an explicit environment list:

```bash
tox -e py313,lint
```

Or set the `TOXENV` environment variable:

```yaml
env:
  TOXENV: py313,lint
```

When you specify environments explicitly, tox-gh respects your choice and skips its own selection logic.

### How to use with uv

Install both tox and tox-gh as uv tools:

```yaml
  - name: Install tox
    run: uv tool install tox --with tox-uv --with tox-gh
```

The `--with` flag ensures tox-gh is available when tox runs.

______________________________________________________________________

## Reference

### Configuration

#### `[gh.python]`

Maps Python version strings to lists of tox environments.

**Type**: `dict[str, list[str]]`

**Location**: The configuration can be placed in `tox.ini` under `[gh] python = ...`, in `tox.toml` under `[gh.python]`,
or in `pyproject.toml` under `[tool.tox.gh.python]`.

**Format** (`tox.toml`):

```toml
[gh.python]
"<version>" = ["<env>", ...]
```

**Format** (`tox.ini`):

```ini
[gh]
python =
    <version> = <env>, ...
```

> **Important**: In `tox.ini`, dict entries under `python` must use `=` as the separator. Do not use `:` — it is treated
> as an INI key-value delimiter and will silently break the mapping.

**Format** (`pyproject.toml`):

```toml
[tool.tox.gh.python]
"<version>" = ["<env>", ...]
```

**Version keys** (in priority order): Freethreaded Python versions use `"3.14t"` or `"3.13t"`. Standard CPython versions
use `"3.14"`, `"3.13"`, `"3.12"`, `"3.11"`, or `"3.10"`. Major-only fallbacks use `"3"`. PyPy versions use
`"pypy-3.13"`, `"pypy-3"`, or `"pypy3"`. Pyston versions use `"piston-3.13"` or `"pyston-3"`.

**Behavior**: The matched environment list **replaces** the tox `env_list` entirely. It does not filter the existing
envlist. When using factored environments, you must specify the full env names (generative syntax like `{50,51}` is
supported).

**Examples** (`tox.toml`):

```toml
# Run one environment per version
[gh.python]
"3.13" = ["py313"]

# Run multiple environments on one version
[gh.python]
"3.13" = ["py313", "type", "lint"]

# Freethreaded Python
[gh.python]
"3.14t" = ["py314t"]
"3.14" = ["py314"]

# Fallback to major version
[gh.python]
"3" = ["py3"]
```

**Examples** (`tox.ini`):

```ini
# Run one environment per version
[gh]
python =
    3.13 = py313

# Run multiple environments on one version
# python =
#     3.13 = py313, type, lint

# Freethreaded Python
# python =
#     3.14t = py314t
#     3.14 = py314

# Fallback to major version
# python =
#     3 = py3
```

### Environment Variables

#### `GITHUB_ACTIONS`

**Required**: Must be `"true"` for the plugin to activate.

Automatically set by GitHub Actions. The plugin does nothing when running locally.

#### `TOX_GH_MAJOR_MINOR`

**Optional**: Override automatic Python version detection.

**Values**: Any string matching a key in `[gh.python]` (e.g., `"3.13"`, `"3.14t"`)

**Use cases**: This variable is useful when using `uv python install` instead of `setup-python`, for freethreaded builds
that need explicit version specification, or when automatic detection fails.

**Example**:

```yaml
env:
  TOX_GH_MAJOR_MINOR: ${{ matrix.python-version }}
```

#### `TOXENV`

**Optional**: Explicitly specify which tox environments to run.

When set, tox-gh is completely bypassed and tox runs the specified environments.

**Example**:

```yaml
env:
  TOXENV: py313,lint
```

### Python Version Detection

The plugin detects the Python version by first checking the `TOX_GH_MAJOR_MINOR` environment variable (highest
priority). If not set, it uses `virtualenv.discovery.py_info.PythonInfo.from_exe()` introspection to check the
`free_threaded` attribute (appending a `t` suffix if true), check the `implementation` (handling PyPy, Pyston, or
CPython), and extract major and minor version numbers.

The detection returns a prioritized list of version keys to try. For freethreaded CPython 3.13, it returns
`["3.13t", "3.13", "3"]`. For standard CPython 3.13, it returns `["3.13", "3"]`. For PyPy 3.13, it returns
`["pypy-3.13", "pypy-3", "pypy3"]`.

The plugin uses the first matching key found in your `[gh.python]` configuration.

### GitHub Actions Integration

#### Log Grouping

The plugin creates collapsible log groups using GitHub Actions commands. The `::group::tox:install` group contains the
package installation phase. Each environment's test run gets its own `::group::tox:{env-name}` group. The `::endgroup::`
command closes the current group. This organization makes long CI logs more readable by sectioning output.

#### Step Summary

When running multiple environments (2 or more), the plugin writes to `$GITHUB_STEP_SUMMARY`. Environment passes are
marked with ✓ `:white_check_mark:: env-name` and failures with ✗ `:negative_squared_cross_mark:: env-name`.
Single-environment runs don't produce summary output.

### Behavior

#### Activation Conditions

The plugin activates when `GITHUB_ACTIONS=true`, no explicit `-e` flag was passed to tox, and the `TOXENV` environment
variable is not set. Otherwise it remains inactive.

#### Environment Selection

When active, the plugin first detects the Python version and returns a prioritized key list. It looks up the first
matching key in the `[gh.python]` mapping, inserts the matching environments into tox's env_list via `MemoryLoader`, and
sets the `TOX_GH_MAJOR_MINOR` environment variable (if not already set) for subprocess inheritance.

#### Subprocess Provisioning

When tox provisions itself (via `requires` in tox config), the matched version key is propagated to the subprocess via
`TOX_GH_MAJOR_MINOR`. This ensures provisioned tox processes apply the same environment filtering.

______________________________________________________________________

## Explanation

### Why tox-gh exists

GitHub Actions workflows typically define a matrix strategy with multiple Python versions:

```yaml
strategy:
  matrix:
    python-version: ['3.13', '3.12', '3.11']
```

Each matrix cell spawns a separate worker. Without tox-gh, you can either run all tox environments on every worker
(which is wasteful and redundant) or manually specify which environments to run via `TOXENV` (which is verbose and
error-prone). tox-gh eliminates both problems by automatically mapping Python versions to appropriate tox environments
based on simple configuration.

### How environment selection works

The plugin hooks into tox's configuration system via `tox_add_core_config`. When tox starts, it checks if running in
GitHub Actions (`GITHUB_ACTIONS=true`), verifies the user hasn't specified explicit environments (respecting `-e` and
`TOXENV`), detects the current Python version via `virtualenv`'s introspection, matches the version against the
`[gh.python]` mapping, and overrides tox's env_list with the matched environments. This happens before tox creates any
environments, so tox never sees the unfiltered list.

### Design decisions

**Why not use tox factors?**

Tox 4's native platform factors (`linux`, `darwin`, `win32`) work well for OS-based selection. However, Python version
factors still require explicitly setting which environments to run. tox-gh provides automatic version-based selection
without workflow boilerplate.

**Why detect Python version instead of reading workflow matrix?**

The workflow matrix is not accessible from inside the tox process. GitHub Actions only exposes it via environment
variables you explicitly pass. Auto-detection means zero required environment variables in simple cases.

**Why propagate version key to subprocesses?**

When tox provisions itself (installs dependencies into an isolated environment and re-invokes), the `MemoryLoader`
override exists only in the parent process. Without propagation, the child tox process would run all environments.
Setting `TOX_GH_MAJOR_MINOR` in `os.environ` makes it inherit automatically.

### Comparison to tox-gh-actions

tox-gh-actions offers more configuration flexibility (`[gh-actions:env]` for arbitrary matrix variables) but requires
tox 3 or 4. tox-gh is simpler (Python version mapping only) and requires tox 4+. For most projects, Python version
mapping is sufficient since tox 4's factor conditions handle other use cases natively.

### Limitations

The plugin only supports Python version-based environment selection and requires tox 4.31 or higher. It does not support
arbitrary workflow matrix variables beyond Python versions. Version detection may fail with unusual Python
installations, in which case you should use the `TOX_GH_MAJOR_MINOR` override.
