from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest.mock import ANY

import pytest

from tox_gh import plugin

if TYPE_CHECKING:
    from pathlib import Path

    from tox.pytest import MonkeyPatch, ToxProjectCreator


@pytest.fixture(autouse=True)
def _clear_env_var(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("TOX_GH_MAJOR_MINOR", raising=False)


def test_gh_not_in_actions(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    project = tox_project({"tox.ini": "[testenv]\npackage=skip"})
    result = project.run("-vv")
    result.assert_success()
    assert "tox-gh won't override envlist because tox is not running in GitHub Actions" in result.out


def test_gh_not_in_actions_quiet(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    project = tox_project({"tox.ini": "[testenv]\npackage=skip"})
    result = project.run()
    result.assert_success()
    assert "tox-gh won't override envlist because tox is not running in GitHub Actions" not in result.out


def test_gh_e_flag_set(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    project = tox_project({"tox.ini": "[testenv]\npackage=skip"})
    result = project.run("-e", "py", "-vv")
    result.assert_success()
    assert "tox-gh won't override envlist because envlist is explicitly given via -e flag" in result.out


def test_gh_toxenv_set(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("TOXENV", "py")
    project = tox_project({"tox.ini": "[testenv]\npackage=skip"})
    result = project.run("-vv")
    result.assert_success()
    assert "tox-gh won't override envlist because envlist is explicitly given via TOXENV" in result.out


@pytest.mark.parametrize("via_env", [True, False])
def test_gh_ok(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator, tmp_path: Path, via_env: bool) -> None:
    if via_env:
        monkeypatch.setenv("TOX_GH_MAJOR_MINOR", f"{sys.version_info.major}.{sys.version_info.minor}")
    else:
        monkeypatch.setenv("PATH", "")
    step_output_file = tmp_path / "gh_out"
    step_output_file.touch()
    empty_requirements = tmp_path / "empty.txt"
    empty_requirements.touch()
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    monkeypatch.setattr(plugin, "GITHUB_STEP_SUMMARY", str(step_output_file))
    ini = f"""
    [testenv]
    package = editable
    deps = -r {empty_requirements}
    [gh]
    python =
        {sys.version_info[0]} = a, b
    """
    project = tox_project({"tox.ini": ini})
    result = project.run()
    result.assert_success()
    assert result.out.splitlines() == [
        "ROOT: running tox-gh",
        "ROOT: tox-gh set a, b",
        "::group::tox:install",
        f"a: install_deps> python -I -m pip install -r {empty_requirements}",
        ANY,  # pip install setuptools wheel
        ANY,  # .pkg: _optional_hooks
        ANY,  # .pkg: get_requires_for_build_editable
        ".pkg: freeze> python -m pip freeze --all",
        ANY,  # freeze list
        ANY,  # .pkg: build_editable
        ANY,  # a: install_package
        "a: freeze> python -m pip freeze --all",
        ANY,  # freeze list
        "::endgroup::",
        "::group::tox:a",
        "::endgroup::",
        ANY,  # a finished
        "::group::tox:install",
        f"b: install_deps> python -I -m pip install -r {empty_requirements}",
        ANY,  # b: install_package
        "b: freeze> python -m pip freeze --all",
        ANY,  # freeze list
        "::endgroup::",
        "::group::tox:b",
        "::endgroup::",
        ANY,  # a status
        ANY,  # b status
        ANY,  # outcome
    ]

    assert "a: OK" in result.out
    assert "b: OK" in result.out

    summary_text = step_output_file.read_text()
    assert ":white_check_mark:: a" in summary_text
    assert ":white_check_mark:: b" in summary_text


def test_gh_fail(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator, tmp_path: Path) -> None:
    step_output_file = tmp_path / "gh_out"
    step_output_file.touch()
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    monkeypatch.setattr(plugin, "GITHUB_STEP_SUMMARY", str(step_output_file))
    ini = f"""
    [testenv]
    package = skip
    commands = python -c exit(1)
    [gh]
    python =
        {sys.version_info[0]} = a, b
    """
    project = tox_project({"tox.ini": ini})
    result = project.run()
    result.assert_failed()

    assert result.out.splitlines() == [
        "ROOT: running tox-gh",
        "ROOT: tox-gh set a, b",
        "::group::tox:install",
        "a: freeze> python -m pip freeze --all",
        ANY,  # freeze list
        "::endgroup::",
        "::group::tox:a",
        ANY,  # "a: commands[0]> python -c 'exit(1)'", but without the quotes on Windows.
        ANY,  # process details
        "::endgroup::",
        ANY,  # a finished
        "::group::tox:install",
        "b: freeze> python -m pip freeze --all",
        ANY,  # freeze list
        "::endgroup::",
        "::group::tox:b",
        ANY,  # "b: commands[0]> python -c 'exit(1)'", but without the quotes on Windows.
        ANY,  # b process details
        "::endgroup::",
        ANY,  # a status
        ANY,  # b status
        ANY,  # outcome
    ]

    assert "a: FAIL code 1" in result.out
    assert "b: FAIL code 1" in result.out

    summary_text = step_output_file.read_text()
    assert ":negative_squared_cross_mark:: a" in summary_text
    assert ":negative_squared_cross_mark:: b" in summary_text
