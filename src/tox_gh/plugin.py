import logging
import os
import shutil
import sys
from typing import Dict, List

from tox.config.loader.memory import MemoryLoader
from tox.config.main import Config
from tox.config.sets import ConfigSet
from tox.config.types import EnvList
from tox.plugin import impl
from virtualenv.discovery.py_info import PythonInfo


class GhActionsConfigSet(ConfigSet):
    SECTION = "gh"

    def __init__(self, conf: Config):
        super().__init__(conf)
        self.add_config("python", of_type=Dict[str, EnvList], default={}, desc="python version to mapping")


def is_running_on_actions() -> bool:
    """Returns True when running on GitHub Actions"""
    # https://docs.github.com/en/actions/reference/environment-variables#default-environment-variables
    return os.environ.get("GITHUB_ACTIONS") == "true"


def get_python_version_keys() -> List[str]:
    """Get Python version in string for getting factors from gh-action's config

    Examples:
    - CPython 2.7.z => [2.7, 2]
    - CPython 3.8.z => [3.8, 3]
    - PyPy 2.7 (v7.3.z) => [pypy-2.7, pypy-2, pypy2]
    - PyPy 3.6 (v7.3.z) => [pypy-3.6, pypy-3, pypy3]
    - Pyston based on Python CPython 3.8.8 (v2.2) => [pyston-3.8, pyston-3]

    Support of "pypy2" and "pypy3" is for backward compatibility with
    tox-gh v2.2.0 and before.
    """
    python_exe = shutil.which("python") or sys.executable
    info = PythonInfo.from_exe(exe=python_exe)
    major_version = str(info.version_info[0])
    major_minor_version = ".".join([str(i) for i in info.version_info[:2]])
    if "PyPy" == info.implementation:
        return [
            f"pypy-{major_minor_version}",
            f"pypy-{major_version}",
            f"pypy{major_version}",
        ]
    elif hasattr(sys, "pyston_version_info"):  # Pyston
        return [
            f"piston-{major_minor_version}",
            f"pyston-{major_version}",
        ]
    else:  # Assume this is running on CPython
        return [
            major_minor_version,
            major_version,
        ]


@impl
def tox_configure(config: Config) -> None:
    bail_reason = None
    if not is_running_on_actions():
        bail_reason = "tox is not running in GitHub Actions"
    elif getattr(config.options.env, "use_default_list", False) is False:
        bail_reason = f"envlist is explicitly given via {'TOXENV'if os.environ.get('TOXENV') else '-e flag'}"
    if bail_reason:
        logging.warning("tox-gh won't override envlist because %s", bail_reason)
        return
    logging.warning("running tox-gh")

    # read the configuration file - gh section in config file
    gh_config = config.get_section_config(GhActionsConfigSet.SECTION, GhActionsConfigSet)
    python_mapping: Dict[str, EnvList] = gh_config["python"]

    py_info = get_python_version_keys()

    env_list = next((python_mapping[i] for i in py_info if i in python_mapping), None)
    if env_list is not None:  # override the env_list core configuration with our values
        logging.warning("tox-gh set %s", ", ".join(env_list))
        config.core.loaders.insert(0, MemoryLoader(env_list=env_list))
