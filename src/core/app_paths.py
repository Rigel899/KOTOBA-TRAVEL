"""
core/app_paths.py
Percorsi dati dell'applicazione — Windows, Linux (XDG), macOS.
"""
from __future__ import annotations

import os
import platform


class AppPaths:
    APP_DIR_NAME = "KotobaTravel"

    @staticmethod
    def data_dir() -> str:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "asset", "data")
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def user_data_dir(cls) -> str:
        system = platform.system()
        if system == "Windows":
            appdata = os.environ.get("APPDATA")
            base = appdata if appdata else os.path.expanduser("~")
            path = os.path.join(base, cls.APP_DIR_NAME)
        elif system == "Darwin":
            path = os.path.join(
                os.path.expanduser("~"), "Library", "Application Support", cls.APP_DIR_NAME
            )
        else:
            # Linux: rispetta XDG_DATA_HOME, default ~/.local/share
            xdg_data = os.environ.get(
                "XDG_DATA_HOME",
                os.path.join(os.path.expanduser("~"), ".local", "share"),
            )
            path = os.path.join(xdg_data, cls.APP_DIR_NAME)
        os.makedirs(path, exist_ok=True)
        return path
