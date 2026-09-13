"""Resolves paths to bundled resources and to writable user data.

Bundled resources (assets) work both when running from source (paths
are relative to the project root) and from a PyInstaller-frozen build,
which extracts bundled data files under a temporary `sys._MEIPASS`
directory instead.

User data (save games, authored levels) can't live alongside either of
those: a frozen build's own directory is typically read-only, and the
process's working directory when a user double-clicks the executable
isn't predictable or guaranteed writable. That data instead goes in
the OS's standard per-user data directory.
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_APP_NAME = "BombFrog"


def resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", _PROJECT_ROOT)
    return os.path.join(base, relative_path)


def _user_data_dir():
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    elif sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    return os.path.join(base, _APP_NAME)


def user_data_path(relative_path):
    return os.path.join(_user_data_dir(), relative_path)
