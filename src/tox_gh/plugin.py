from __future__ import annotations

import logging
import os
import shutil
import sys
from typing import Dict

from tox.config.loader.memory import MemoryLoader
from tox.config.loader.section import Section
from tox.config.sets import ConfigSet
from tox.config.types import EnvList
from tox.execute import Outcome
from tox.plugin import impl
from tox.session.state import State
from tox.tox_env.api import ToxEnv
from virtualenv.discovery.py_info import PythonInfo  # type: ignore # no types defined


def is_running_on_actions() -> bool:
    """:return: True if running on Github Actions platform"""
    # https://docs.github.com/en/actions/reference/environment-variables#default-environment-variables
    return os.environ.get("GITHUB_ACTIONS") == "true"


def get_python_version_keys() -> list[str]:
    """:return: python spec for the python interpreter"""
    python_exe = shutil.which("python") or sys.executable
    info = PythonInfo.from_exe(exe=python_exe)
    major_version = str(info.version_info[0])
    major_minor_version = ".".join([str(i) for i in info.version_info[:2]])
    if "PyPy" == info.implementation:
        return [f"pypy-{major_minor_version}", f"pypy-{major_version}", f"pypy{major_version}"]
    elif hasattr(sys, "pyston_version_info"):  # Pyston
        return [f"piston-{major_minor_version}", f"pyston-{major_version}"]
    else:  # Assume this is running on CPython
        return [major_minor_version, major_version]


class GhActionsConfigSet(ConfigSet):
    def register_config(self) -> None:
        self.add_config("python", of_type=Dict[str, EnvList], default={}, desc="python version to mapping")


@impl
def tox_add_core_config(core_conf: ConfigSet, state: State) -> None:
    core_conf.add_constant(keys="is_on_gh_action", desc="flag for running on Github", value=is_running_on_actions())

    bail_reason = None
    if not core_conf["is_on_gh_action"]:
        bail_reason = "tox is not running in GitHub Actions"
    elif getattr(state.conf.options.env, "is_default_list", False) is False:
        bail_reason = f"envlist is explicitly given via {'TOXENV'if os.environ.get('TOXENV') else '-e flag'}"
    if bail_reason:
        logging.warning("tox-gh won't override envlist because %s", bail_reason)
        return

    logging.warning("running tox-gh")
    gh_config = state.conf.get_section_config(Section(None, "gh"), base=[], of_type=GhActionsConfigSet, for_env=None)
    python_mapping: dict[str, EnvList] = gh_config["python"]

    env_list = next((python_mapping[i] for i in get_python_version_keys() if i in python_mapping), None)
    if env_list is not None:  # override the env_list core configuration with our values
        logging.warning("tox-gh set %s", ", ".join(env_list))
        state.conf.core.loaders.insert(0, MemoryLoader(env_list=env_list))


@impl
def tox_before_run_commands(tox_env: ToxEnv) -> None:
    if tox_env.core["is_on_gh_action"]:
        print(f"::group::tox:{tox_env.name}")


@impl
def tox_after_run_commands(tox_env: ToxEnv, exit_code: int, outcomes: list[Outcome]) -> None:  # noqa: U100
    if tox_env.core["is_on_gh_action"]:
        print("::endgroup::")
