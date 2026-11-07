"""GitHub Actions integration."""

from __future__ import annotations

import logging
import os
import pathlib
import shutil
import sys
import threading
from typing import TYPE_CHECKING, Any, Final, cast

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from tox.config.loader.ini.factor import extend_factors
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

GITHUB_STEP_SUMMARY: Final[str] = os.getenv("GITHUB_STEP_SUMMARY", "")
_WILL_RUN_MULTIPLE_ENVS = False


@impl
def tox_add_core_config(core_conf: ConfigSet, state: State) -> None:
    """
    Add core configuration flags.

    :param core_conf: the core configuration
    :param state: tox state object
    """
    global _WILL_RUN_MULTIPLE_ENVS  # ruff:ignore[global-statement] shared with tox_after_run_commands

    # https://docs.github.com/en/actions/reference/environment-variables#default-environment-variables
    core_conf.add_constant(
        keys="is_on_gh_action", desc="flag for running on Github", value=os.environ.get("GITHUB_ACTIONS") == "true"
    )

    bail_reason = None
    if not core_conf["is_on_gh_action"]:
        bail_reason = "tox is not running in GitHub Actions"
    elif getattr(state.conf.options.env, "is_default_list", False) is False:
        bail_reason = f"envlist is explicitly given via {'TOXENV' if os.environ.get('TOXENV', '') else '-e flag'}"
    if bail_reason is not None:
        logging.debug("tox-gh won't override envlist because %s", bail_reason)
        return

    logging.warning("running tox-gh")
    gh_config = state.conf.get_section_config(Section(None, "gh"), base=[], of_type=_GhActionsConfigSet, for_env=None)
    python_mapping = cast("dict[str, EnvList]", gh_config["python"])

    python_version_keys = get_python_version_keys()
    if (
        env_list := next((python_mapping[i] for i in python_version_keys if i in python_mapping), None)
    ) is not None:  # override the env_list core configuration with our values
        env_list = EnvList([env for expression in env_list for env in extend_factors(expression)])
        logging.warning("tox-gh set %s", ", ".join(env_list))
        state.conf.core.loaders.insert(0, MemoryLoader(env_list=env_list))
        _WILL_RUN_MULTIPLE_ENVS = len(env_list.envs) > 1
        if not os.environ.get("TOX_GH_MAJOR_MINOR", ""):
            os.environ["TOX_GH_MAJOR_MINOR"] = next(i for i in python_version_keys if i in python_mapping)


class _GhActionsConfigSet(ConfigSet):
    @override
    def register_config(self) -> None:
        self.add_config(
            "python",
            of_type=dict[str, EnvList],
            default={},
            desc="python version to mapping",
        )


def get_python_version_keys() -> list[str]:
    """
    Get the python spec keys matching the running interpreter.

    :returns: python spec keys, most specific first
    :raises RuntimeError: if the Python version cannot be detected
    """
    if os.environ.get("TOX_GH_MAJOR_MINOR", ""):
        major_minor_version = os.environ["TOX_GH_MAJOR_MINOR"]
        return [major_minor_version, major_minor_version.split(".")[0]]
    python_exe = shutil.which("python") or sys.executable
    if (info := PythonInfo.from_exe(exe=python_exe)) is None:
        msg = f"failed to detect Python version from {python_exe}, set TOX_GH_MAJOR_MINOR environment variable"
        raise RuntimeError(msg)
    major_version = str(info.version_info[0])
    major_minor_version = ".".join([str(i) for i in info.version_info[:2]])
    if info.implementation == "PyPy":
        return [f"pypy-{major_minor_version}", f"pypy-{major_version}", f"pypy{major_version}"]
    if hasattr(sys, "pyston_version_info"):  # Pyston
        return [f"piston-{major_minor_version}", f"pyston-{major_version}"]
    if getattr(info, "free_threaded", False):
        return [f"{major_minor_version}t", major_minor_version, major_version]
    return [major_minor_version, major_version]


_STATE: Final[threading.local] = threading.local()


@impl
def tox_on_install(tox_env: ToxEnv, arguments: Any, section: str, of_type: str) -> None:  # ruff:ignore[any-type, unused-function-argument] tox's hook spec fixes the signature
    """
    Run before installing to prepare an environment.

    :param tox_env: the tox environment
    :param arguments: installation arguments
    :param section: section of the installation
    :param of_type: type of the installation
    """
    if tox_env.core["is_on_gh_action"] and not getattr(_STATE, "installing", False):
        _STATE.installing = True
        print("::group::tox:install")  # ruff:ignore[print] GitHub reads workflow commands from stdout


@impl
def tox_before_run_commands(tox_env: ToxEnv) -> None:
    """
    Run logic before tox run commands.

    :param tox_env: the tox environment
    """
    if tox_env.core["is_on_gh_action"]:
        # Check if we're coming from an install phase (defensive check for lock-based runners)
        if getattr(_STATE, "installing", False):
            # Traditional path: close the install group that was opened in tox_on_install
            _STATE.installing = False
            print("::endgroup::")  # ruff:ignore[print] GitHub reads workflow commands from stdout
        # Always open the test execution group
        print(f"::group::tox:{tox_env.name}")  # ruff:ignore[print] GitHub reads workflow commands from stdout


@impl
def tox_after_run_commands(tox_env: ToxEnv, exit_code: int, outcomes: list[Outcome]) -> None:  # ruff:ignore[unused-function-argument] tox's hook spec fixes the signature
    """
    Run logic before after run commands.


    :param tox_env: the tox environment
    :param exit_code: command exit code
    :param outcomes: list of outcomes
    """
    if tox_env.core["is_on_gh_action"]:
        print("::endgroup::")  # ruff:ignore[print] GitHub reads workflow commands from stdout
        if _WILL_RUN_MULTIPLE_ENVS:
            _write_to_summary(exit_code == Outcome.OK, tox_env.name)


def _write_to_summary(success: bool, message: str) -> None:  # ruff:ignore[boolean-type-hint-positional-argument] the flag reads as the run outcome at the call site
    # Write a success or failure value to the GitHub step summary if it exists.
    #
    # :param success:
    # :param message:
    if not GITHUB_STEP_SUMMARY:
        return
    summary_path = pathlib.Path(GITHUB_STEP_SUMMARY)
    success_str = ":white_check_mark:" if success else ":negative_squared_cross_mark:"
    with summary_path.open("a+", encoding="utf-8") as summary_file:
        print(f"{success_str}: {message}", file=summary_file)


__all__ = [
    "get_python_version_keys",
]
