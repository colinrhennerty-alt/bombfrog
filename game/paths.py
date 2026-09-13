"""Resolves paths to bundled resources (assets, not user data).

Works both when running from source (paths are relative to the project
root) and from a PyInstaller-frozen build, which extracts bundled data
files under a temporary `sys._MEIPASS` directory instead.
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", _PROJECT_ROOT)
    return os.path.join(base, relative_path)
