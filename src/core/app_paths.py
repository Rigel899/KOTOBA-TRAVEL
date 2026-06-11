"""
core/app_paths.py
Percorsi dati dell'applicazione.
"""
from __future__ import annotations

import os


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
        appdata = os.environ.get("APPDATA")
        if appdata:
            path = os.path.join(appdata, cls.APP_DIR_NAME)
        else:
            path = os.path.join(os.path.expanduser("~"), ".kotoba_travel")
        os.makedirs(path, exist_ok=True)
        return path
