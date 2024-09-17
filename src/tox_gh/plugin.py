"""GitHub Actions integration."""

from __future__ import annotations

import logging
import os
import pathlib
import shutil
import sys
import threading
from typing import TYPE_CHECKING, Any, Dict

from tox.config.loader.memory import MemoryLoader
from tox.config.loader.section import Section
from tox.config.sets import ConfigSet
from tox.config.types import EnvList
from tox.execute import Outcome
from tox.plugin import impl
from virtualenv.discovery.py_info import PythonInfo

if TYPE_CHECKING:
    from tox.session.state import State
    from tox.tox_env.api import ToxEnv

GITHUB_STEP_SUMMARY = os.getenv("GITHUB_STEP_SUMMARY")


def is_running_on_actions() -> bool:
    """:return: True if running on GitHub Actions platform"""
    # https://docs.github.com/en/actions/reference/environment-variables#default-environment-variables
    return os.environ.get("GITHUB_ACTIONS") == "true"


def get_python_version_keys() -> list[str]:
    """:return: python spec for the python interpreter"""
    if os.environ.get("TOX_GH_MAJOR_MINOR"):
        major_minor_version = os.environ["TOX_GH_MAJOR_MINOR"]
        return [major_minor_version, major_minor_version.split(".")[0]]
    python_exe = shutil.which("python") or sys.executable
    info = PythonInfo.from_exe(exe=python_exe)
    major_version = str(info.version_info[0])
    major_minor_version = ".".join([str(i) for i in info.version_info[:2]])
    if info.implementation == "PyPy":
        return [f"pypy-{major_minor_version}", f"pypy-{major_version}", f"pypy{major_version}"]
    if hasattr(sys, "pyston_version_info"):  # Pyston
        return [f"piston-{major_minor_version}", f"pyston-{major_version}"]
    # Assume this is running on CPython
    return [major_minor_version, major_version]


class GhActionsConfigSet(ConfigSet):
    """GitHub Actions config set."""

    def register_config(self) -> None:
        """Register the configurations."""
        self.add_config("python", of_type=Dict[str, EnvList], default={}, desc="python version to mapping")


@impl
def tox_add_core_config(core_conf: ConfigSet, state: State) -> None:
    """
    Add core configuration flags.

    :param core_conf: the core configuration
    :param state: tox state object
    """
    core_conf.add_constant(keys="is_on_gh_action", desc="flag for running on Github", value=is_running_on_actions())

    bail_reason = None
    if not core_conf["is_on_gh_action"]:
        bail_reason = "tox is not running in GitHub Actions"
    elif getattr(state.conf.options.env, "is_default_list", False) is False:
        bail_reason = f"envlist is explicitly given via {'TOXENV' if os.environ.get('TOXENV') else '-e flag'}"
    if bail_reason:
        logging.debug("tox-gh won't override envlist because %s", bail_reason)
        return

    logging.warning("running tox-gh")
    gh_config = state.conf.get_section_config(Section(None, "gh"), base=[], of_type=GhActionsConfigSet, for_env=None)
    python_mapping: dict[str, EnvList] = gh_config["python"]

    env_list = next((python_mapping[i] for i in get_python_version_keys() if i in python_mapping), None)
    if env_list is not None:  # override the env_list core configuration with our values
        logging.warning("tox-gh set %s", ", ".join(env_list))
        state.conf.core.loaders.insert(0, MemoryLoader(env_list=env_list))


_STATE = threading.local()


@impl
def tox_on_install(tox_env: ToxEnv, arguments: Any, section: str, of_type: str) -> None:  # noqa: ANN401, ARG001
    """
    Run before installing to prepare an environment.

    :param tox_env: the tox environment
    :param arguments: installation arguments
    :param section: section of the installation
    :param of_type: type of the installation
    """
    if tox_env.core["is_on_gh_action"]:
        installing = getattr(_STATE, "installing", False)
        if not installing:
            _STATE.installing = True
            print("::group::tox:install")  # noqa: T201


@impl
def tox_before_run_commands(tox_env: ToxEnv) -> None:
    """
    Run logic before tox run commands.

    :param tox_env: the tox environment
    """
    if tox_env.core["is_on_gh_action"]:
        assert _STATE.installing  # noqa: S101
        _STATE.installing = False
        print("::endgroup::")  # noqa: T201
        print(f"::group::tox:{tox_env.name}")  # noqa: T201


@impl
def tox_after_run_commands(tox_env: ToxEnv, exit_code: int, outcomes: list[Outcome]) -> None:  # noqa: ARG001
    """
    Run logic before after run commands.


    :param tox_env: the tox environment
    :param exit_code: command exit code
    :param outcomes: list of outcomes
    """
    if tox_env.core["is_on_gh_action"]:
        print("::endgroup::")  # noqa: T201
        write_to_summary(exit_code == Outcome.OK, tox_env.name)


def write_to_summary(success: bool, message: str) -> None:  # noqa: FBT001
    """Write a success or failure value to the GitHub step summary if it exists."""
    if not GITHUB_STEP_SUMMARY:
        return
    summary_path = pathlib.Path(GITHUB_STEP_SUMMARY)
    success_str = ":white_check_mark:" if success else ":negative_squared_cross_mark:"
    with summary_path.open("a+") as summary_file:
        print(f"{success_str}: {message}", file=summary_file)
