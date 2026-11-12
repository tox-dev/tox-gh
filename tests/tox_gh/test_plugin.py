from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import pytest
from virtualenv.discovery.py_info import PythonInfo

from tox_gh import plugin
from tox_gh.plugin import (
    GITHUB_STEP_SUMMARY,
    WILL_RUN_MULTIPLE_ENVS,
    GhActionsConfigSet,
    get_python_version_keys,
    is_running_on_actions,
    write_to_summary,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from pytest_mock import MockerFixture
    from tox.pytest import MonkeyPatch, ToxProjectCreator


@pytest.fixture(autouse=True)
def _clear_env_var(monkeypatch: MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("TOX_GH_MAJOR_MINOR", raising=False)
    yield
    # the plugin exports the variable itself, and tox's environment check runs before monkeypatch restores it
    os.environ.pop("TOX_GH_MAJOR_MINOR", None)


@pytest.fixture
def summary_output_path(monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
    path = tmp_path / "gh_out"
    path.touch()
    monkeypatch.setattr(plugin, "GITHUB_STEP_SUMMARY", str(path))
    return path


def test_public_imports() -> None:
    namespace = {}
    exec("from tox_gh.plugin import *", namespace)  # ruff:ignore[exec-builtin] exercise wildcard imports
    assert namespace["GITHUB_STEP_SUMMARY"] is GITHUB_STEP_SUMMARY
    assert namespace["GhActionsConfigSet"] is GhActionsConfigSet
    assert namespace["WILL_RUN_MULTIPLE_ENVS"] is WILL_RUN_MULTIPLE_ENVS
    assert namespace["get_python_version_keys"] is get_python_version_keys
    assert namespace["is_running_on_actions"] is is_running_on_actions
    assert namespace["tox_add_core_config"] is plugin.tox_add_core_config
    assert namespace["tox_after_run_commands"] is plugin.tox_after_run_commands
    assert namespace["tox_before_run_commands"] is plugin.tox_before_run_commands
    assert namespace["tox_on_install"] is plugin.tox_on_install
    assert namespace["write_to_summary"] is write_to_summary
    assert "logging" not in namespace


def test_is_running_on_actions(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert is_running_on_actions()
    monkeypatch.setenv("GITHUB_ACTIONS", "false")
    assert not is_running_on_actions()


def test_write_to_summary(summary_output_path: Path) -> None:
    for success, message in ((True, "passed"), (False, "failed")):
        write_to_summary(success, message)
    assert summary_output_path.read_text(encoding="utf-8") == (
        ":white_check_mark:: passed\n:negative_squared_cross_mark:: failed\n"
    )


def test_gh_not_in_actions(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    result = tox_project({"tox.ini": "[testenv]\npackage=skip"}).run("-vv")
    result.assert_success()
    assert "tox-gh won't override envlist because tox is not running in GitHub Actions" in result.out


def test_gh_not_in_actions_quiet(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    result = tox_project({"tox.ini": "[testenv]\npackage=skip"}).run()
    result.assert_success()
    assert "tox-gh won't override envlist because tox is not running in GitHub Actions" not in result.out


def test_gh_e_flag_set(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    result = tox_project({"tox.ini": "[testenv]\npackage=skip"}).run("-e", "py", "-vv")
    result.assert_success()
    assert "tox-gh won't override envlist because envlist is explicitly given via -e flag" in result.out


def test_gh_toxenv_set(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("TOXENV", "py")
    result = tox_project({"tox.ini": "[testenv]\npackage=skip"}).run("-vv")
    result.assert_success()
    assert "tox-gh won't override envlist because envlist is explicitly given via TOXENV" in result.out


def test_gh_no_matching_python_mapping(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    result = tox_project({"tox.ini": "[testenv]\npackage=skip\n[gh]\npython=\n    0=a"}).run()
    result.assert_success()
    assert "running tox-gh" in result.out
    assert "tox-gh set" not in result.out


@pytest.mark.parametrize(
    "version_env",
    [
        pytest.param(f"{sys.version_info.major}.{sys.version_info.minor}", id="env-var"),
        pytest.param("", id="detected"),
    ],
)
def test_gh_ok(
    monkeypatch: MonkeyPatch,
    mocker: MockerFixture,
    tox_project: ToxProjectCreator,
    summary_output_path: Path,
    version_env: str,
) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("PATH", "")
    monkeypatch.setenv("TOX_GH_MAJOR_MINOR", version_env)
    monkeypatch.delenv("TOXENV", raising=False)
    ini = f"""
    [testenv]
    package = editable
    deps = -r empty.txt
    [gh]
    python =
        {sys.version_info[0]} = a, b
    """
    result = tox_project({"tox.ini": ini, "empty.txt": ""}).run()
    result.assert_success()
    assert result.out.splitlines() == [
        "ROOT: running tox-gh",
        "ROOT: tox-gh set a, b",
        "::group::tox:install",
        "a: install_deps> python -I -m pip install -r empty.txt",
        mocker.ANY,  # pip install setuptools wheel
        mocker.ANY,  # .pkg: _optional_hooks
        mocker.ANY,  # .pkg: get_requires_for_build_editable
        ".pkg: freeze> python -m pip freeze --all",
        mocker.ANY,  # freeze list
        mocker.ANY,  # .pkg: build_editable
        mocker.ANY,  # a: install_package
        "a: freeze> python -m pip freeze --all",
        mocker.ANY,  # freeze list
        "::endgroup::",
        "::group::tox:a",
        "::endgroup::",
        mocker.ANY,  # a finished
        "::group::tox:install",
        "b: install_deps> python -I -m pip install -r empty.txt",
        mocker.ANY,  # b: install_package
        "b: freeze> python -m pip freeze --all",
        mocker.ANY,  # freeze list
        "::endgroup::",
        "::group::tox:b",
        "::endgroup::",
        mocker.ANY,  # a status
        mocker.ANY,  # b status
        mocker.ANY,  # outcome
    ]

    assert "a: OK" in result.out
    assert "b: OK" in result.out

    summary_text = summary_output_path.read_text(encoding="utf-8")
    assert ":white_check_mark:: a" in summary_text
    assert ":white_check_mark:: b" in summary_text


def test_gh_fail(
    monkeypatch: MonkeyPatch, mocker: MockerFixture, tox_project: ToxProjectCreator, summary_output_path: Path
) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    ini = f"""
    [testenv]
    package = skip
    commands = python -c exit(1)
    [gh]
    python =
        {sys.version_info[0]} = a, b
    """
    result = tox_project({"tox.ini": ini}).run()
    result.assert_failed()

    assert result.out.splitlines() == [
        "ROOT: running tox-gh",
        "ROOT: tox-gh set a, b",
        "::group::tox:install",
        "a: freeze> python -m pip freeze --all",
        mocker.ANY,  # freeze list
        "::endgroup::",
        "::group::tox:a",
        mocker.ANY,  # "a: commands[0]> python -c 'exit(1)'", but without the quotes on Windows.
        mocker.ANY,  # process details
        "::endgroup::",
        mocker.ANY,  # a finished
        "::group::tox:install",
        "b: freeze> python -m pip freeze --all",
        mocker.ANY,  # freeze list
        "::endgroup::",
        "::group::tox:b",
        mocker.ANY,  # "b: commands[0]> python -c 'exit(1)'", but without the quotes on Windows.
        mocker.ANY,  # b process details
        "::endgroup::",
        mocker.ANY,  # a status
        mocker.ANY,  # b status
        mocker.ANY,  # outcome
    ]

    assert "a: FAIL code 1" in result.out
    assert "b: FAIL code 1" in result.out

    summary_text = summary_output_path.read_text(encoding="utf-8")
    assert ":negative_squared_cross_mark:: a" in summary_text
    assert ":negative_squared_cross_mark:: b" in summary_text


def test_gh_single_env_ok(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator, summary_output_path: Path) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    ini = f"""
    [testenv]
    package = editable
    [gh]
    python =
        {sys.version_info[0]} = a
    """
    tox_project({"tox.ini": ini}).run().assert_success()

    summary_text = summary_output_path.read_text(encoding="utf-8")
    assert len(summary_text) == 0


def test_gh_expands_toml_factors(
    monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator, summary_output_path: Path
) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    project = tox_project({
        "tox.toml": f"""
            [tox]
            env_list = [{{ product = [["unit", "lint"], ["{version}"]] }}]

            [env_run_base]
            package = "skip"

            [gh.python]
            "{version}" = ["{{unit,lint}}-{version}"]
            """,
    })
    result = project.run()
    result.assert_success()
    assert f"ROOT: tox-gh set unit-{version}, lint-{version}" in result.out
    assert f"unit-{version}: OK" in result.out
    assert f"lint-{version}: OK" in result.out
    assert summary_output_path.read_text(encoding="utf-8").splitlines() == [
        f":white_check_mark:: unit-{version}",
        f":white_check_mark:: lint-{version}",
    ]


@pytest.mark.parametrize(
    ("free_threaded", "expected"),
    [
        pytest.param(True, ["3.13t", "3.13", "3"], id="freethreaded"),
        pytest.param(False, ["3.13", "3"], id="standard"),
    ],
)
def test_freethreaded_python_detection(
    monkeypatch: MonkeyPatch, mocker: MockerFixture, *, free_threaded: bool, expected: list[str]
) -> None:
    monkeypatch.delenv("TOX_GH_MAJOR_MINOR", raising=False)
    mock_info = mocker.create_autospec(
        PythonInfo,
        instance=True,
        version_info=(3, 13, 1, "final", 0),
        implementation="CPython",
        free_threaded=free_threaded,
    )
    mocker.patch.object(PythonInfo, "from_exe", autospec=True, return_value=mock_info)
    result = get_python_version_keys()
    assert result == expected


def test_python_detection_fails(monkeypatch: MonkeyPatch, mocker: MockerFixture) -> None:
    monkeypatch.delenv("TOX_GH_MAJOR_MINOR", raising=False)
    mocker.patch.object(PythonInfo, "from_exe", autospec=True, return_value=None)
    with pytest.raises(RuntimeError, match="failed to detect Python version"):
        get_python_version_keys()


def test_override_sets_tox_gh_major_minor(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    ini = f"""
    [testenv]
    package = skip
    [gh]
    python =
        {sys.version_info[0]}.{sys.version_info[1]} = a
    """
    result = tox_project({"tox.ini": ini}).run()
    result.assert_success()
    assert "tox-gh set a" in result.out
    assert os.environ.get("TOX_GH_MAJOR_MINOR") == f"{sys.version_info[0]}.{sys.version_info[1]}"


def test_gh_single_env_fail(
    monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator, summary_output_path: Path
) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
    ini = f"""
    [testenv]
    package = skip
    commands = python -c exit(1)
    [gh]
    python =
        {sys.version_info[0]} = a
    """
    tox_project({"tox.ini": ini}).run().assert_failed()

    summary_text = summary_output_path.read_text(encoding="utf-8")
    assert len(summary_text) == 0
