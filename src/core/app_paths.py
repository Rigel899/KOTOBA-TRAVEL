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
    def asset_dir() -> str:
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(src_dir, "asset")

    @staticmethod
    def data_dir() -> str:
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        real = os.path.join(os.path.dirname(src_dir), "_dati_reali", "data")
        if os.path.isdir(real):
            return real
        path = os.path.join(src_dir, "asset", "data")
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def food_image_abs(relative_path: str) -> str:
        """Restituisce il path assoluto di un'immagine food.

        Controlla prima _dati_reali/images/food/ (dev con dati reali),
        poi fallback su src/asset/ (demo o release build).
        """
        if not relative_path:
            return ""
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        real_food = os.path.join(
            os.path.dirname(src_dir), "_dati_reali", "images", "food",
            os.path.basename(relative_path),
        )
        if os.path.isfile(real_food):
            return real_food
        return os.path.join(src_dir, "asset", relative_path)

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
