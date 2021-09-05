import sys

from tox.pytest import MonkeyPatch, ToxProjectCreator


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


def test_gh_ok(monkeypatch: MonkeyPatch, tox_project: ToxProjectCreator) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("TOXENV", raising=False)
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

    assert "ROOT: running tox-gh" in result.out
    assert "ROOT: tox-gh set a, b" in result.out
    assert "a: OK" in result.out
    assert "b: OK" in result.out
