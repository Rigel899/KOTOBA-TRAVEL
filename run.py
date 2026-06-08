import flet as ft
from src.main import main, before_main, ASSETS_DIR

if __name__ == "__main__":
    ft.run(main, before_main=before_main, assets_dir=ASSETS_DIR)