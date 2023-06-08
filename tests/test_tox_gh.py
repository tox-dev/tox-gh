from __future__ import annotations

import pathlib
import sys
from unittest.mock import ANY

from tox.pytest import MonkeyPatch, ToxProjectCreator

from tox_gh import plugin


def test_gh_not_in_actions(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    project = tox_project({"tox.ini": "[testenv]\npackage=skip"})
    result = project.run()
    result.assert_success()
    assert "ROOT: tox-gh won't override envlist because tox is not running in GitHub Actions" in result.out


def test_gh_e_flag_set(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    project = tox_project({"tox.ini": "[testenv]\npackage=skip"})
    result = project.run("-e", "py")
    result.assert_success()
    assert "tox-gh won't override envlist because envlist is explicitly given via -e flag" in result.out


def test_gh_toxenv_set(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("TOXENV", "py")
    project = tox_project({"tox.ini": "[testenv]\npackage=skip"})
    result = project.run()
    result.assert_success()
    assert "tox-gh won't override envlist because envlist is explicitly given via TOXENV" in result.out


def test_gh_ok(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator, tmp_path: pathlib.Path) -> None:
    step_output_file = tmp_path / "gh_out"
    step_output_file.touch()
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    monkeypatch.setattr(plugin, "GITHUB_STEP_SUMMARY", str(step_output_file))
    ini = f"""
    [testenv]
    package = skip
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
        "a: freeze> python -m pip freeze --all",
        ANY,  # freeze list
        "::group::tox:a",
        "::endgroup::",
        ANY,  # a finished
        "b: freeze> python -m pip freeze --all",
        ANY,  # freeze list
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


def test_gh_fail(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator, tmp_path: pathlib.Path) -> None:
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
        "a: freeze> python -m pip freeze --all",
        ANY,  # freeze list
        "::group::tox:a",
        "a: commands[0]> python -c 'exit(1)'",
        ANY,  # process details
        "::endgroup::",
        ANY,  # a finished
        "b: freeze> python -m pip freeze --all",
        ANY,  # freeze list
        "::group::tox:b",
        "b: commands[0]> python -c 'exit(1)'",
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
