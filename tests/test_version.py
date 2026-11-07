from __future__ import annotations


def test_version() -> None:
    from tox_gh import __version__  # ruff:ignore[import-outside-top-level] the test checks the package imports

    assert __version__
