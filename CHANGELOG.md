# Changelog

<!-- towncrier release notes start -->

<a name="release-1-9-1"></a>

## 1.9.1 (2026-10-27)

<a name="release-1-9-1-fixed"></a>

### Fixed

- Fix repository links in the PyPI project description ([#310](https://github.com/tox-dev/tox-gh/pull/310)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-9-0"></a>

## 1.9.0 (2026-10-10)

<a name="release-1-9-0-added"></a>

### Added

- Require Python 3.11 ([#305](https://github.com/tox-dev/tox-gh/pull/305)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-9-0-changes"></a>

### Changes

- Use Python 3.15 by default ([#305](https://github.com/tox-dev/tox-gh/pull/305)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-8-0"></a>

## 1.8.0 (2026-07-21)

<a name="release-1-8-0-added"></a>

### Added

- Support Python 3.15 ([#282](https://github.com/tox-dev/tox-gh/pull/282)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-8-0-fixed"></a>

### Fixed

- Report an error when the Python version cannot be detected ([#246](https://github.com/tox-dev/tox-gh/pull/246)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-8-0-documentation"></a>

### Documentation

- Add tox.ini configuration examples ([#246](https://github.com/tox-dev/tox-gh/pull/246)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-7-1"></a>

## 1.7.1 (2026-02-23)

<a name="release-1-7-1-documentation"></a>

### Documentation

- Organize the README by task and reference ([#238](https://github.com/tox-dev/tox-gh/pull/238)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-7-0"></a>

## 1.7.0 (2026-02-23)

<a name="release-1-7-0-added"></a>

### Added

- Detect free-threaded Python variants ([#236](https://github.com/tox-dev/tox-gh/pull/236)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-7-0-fixed"></a>

### Fixed

- Persist Python version keys for provisioned subprocesses ([#237](https://github.com/tox-dev/tox-gh/pull/237)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-6-1"></a>

## 1.6.1 (2025-12-12)

<a name="release-1-6-1-fixed"></a>

### Fixed

- Handle runners that bypass the tox_on_install hook ([#222](https://github.com/tox-dev/tox-gh/pull/222)) by
  [@huynguyengl99](https://github.com/huynguyengl99).

<a name="release-1-6-1-documentation"></a>

### Documentation

- Show Python 3.14 and 3.14t in the examples ([#210](https://github.com/tox-dev/tox-gh/pull/210)) by
  [@cclauss](https://github.com/cclauss).

<a name="release-1-6-0"></a>

## 1.6.0 (2025-10-09)

<a name="release-1-6-0-added"></a>

### Added

- Support Python 3.14 ([#209](https://github.com/tox-dev/tox-gh/pull/209)) by
  [@gaborbernat](https://github.com/gaborbernat).
- End support for Python 3.9 ([#209](https://github.com/tox-dev/tox-gh/pull/209)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-5-0"></a>

## 1.5.0 (2025-01-16)

<a name="release-1-5-0-changes"></a>

### Changes

- Omit the GitHub summary when only one tox environment runs ([#166](https://github.com/tox-dev/tox-gh/pull/166)) by
  [@kemzeb](https://github.com/kemzeb) and [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-4-4"></a>

## 1.4.4 (2024-10-10)

<a name="release-1-4-4-documentation"></a>

### Documentation

- Add a minimal configuration example ([#145](https://github.com/tox-dev/tox-gh/pull/145)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-4-3"></a>

## 1.4.3 (2024-10-10)

<a name="release-1-4-3-documentation"></a>

### Documentation

- Simplify the configuration example ([#144](https://github.com/tox-dev/tox-gh/pull/144)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-4-2"></a>

## 1.4.2 (2024-10-10)

<a name="release-1-4-2-documentation"></a>

### Documentation

- Use tox.toml in the configuration example ([#143](https://github.com/tox-dev/tox-gh/pull/143)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-4-1"></a>

## 1.4.1 (2024-09-17)

<a name="release-1-4-1-documentation"></a>

### Documentation

- Update the Python environment mapping example by [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-4-0"></a>

## 1.4.0 (2024-09-17)

<a name="release-1-4-0-added"></a>

### Added

- Allow the Python major and minor version to be set before environment selection
  ([#134](https://github.com/tox-dev/tox-gh/pull/134)) by [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-3-3"></a>

## 1.3.3 (2024-09-08)

<a name="release-1-3-3-added"></a>

### Added

- Support Python 3.13 ([#128](https://github.com/tox-dev/tox-gh/pull/128)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-3-2"></a>

## 1.3.2 (2024-06-22)

<a name="release-1-3-1"></a>

## 1.3.1 (2023-07-25)

<a name="release-1-3-1-fixed"></a>

### Fixed

- Avoid a warning when tox-gh selects the configured environments ([#77](https://github.com/tox-dev/tox-gh/pull/77)) by
  [@nedbat](https://github.com/nedbat).

<a name="release-1-3-0"></a>

## 1.3.0 (2023-07-23)

<a name="release-1-3-0-changes"></a>

### Changes

- Collapse installation preliminaries in the GitHub Actions log ([#75](https://github.com/tox-dev/tox-gh/pull/75)) by
  [@nedbat](https://github.com/nedbat).

<a name="release-1-2-0"></a>

## 1.2.0 (2023-06-11)

<a name="release-1-2-0-added"></a>

### Added

- Support Python 3.12 ([#65](https://github.com/tox-dev/tox-gh/pull/65)) by
  [@gaborbernat](https://github.com/gaborbernat).

<a name="release-1-1-0"></a>

## 1.1.0 (2023-06-11)

<a name="release-1-1-0-added"></a>

### Added

- Add a summary to each step run ([#63](https://github.com/tox-dev/tox-gh/pull/63)) by
  [@lengau](https://github.com/lengau).

<a name="release-1-0-0"></a>

## 1.0.0 (2023-01-13)

<a name="release-0-0-4"></a>

## 0.0.4 (2022-01-08)

<a name="release-0-0-4-fixed"></a>

### Fixed

- Adapt to tox 4.0.0a10 by [@gaborbernat](https://github.com/gaborbernat).

<a name="release-0-0-3"></a>

## 0.0.3 (2021-09-17)

<a name="release-0-0-3-added"></a>

### Added

- Support Python 3.10 by [@gaborbernat](https://github.com/gaborbernat).

<a name="release-0-0-2"></a>

## 0.0.2 (2021-09-17)

<a name="release-0-0-2-added"></a>

### Added

- Add a tox run group by [@gaborbernat](https://github.com/gaborbernat).

<a name="release-0-0-1"></a>

## 0.0.1 (2021-09-17)

<a name="release-0-0-1-added"></a>

### Added

- Publish the initial tox-gh plugin by [@gaborbernat](https://github.com/gaborbernat).
