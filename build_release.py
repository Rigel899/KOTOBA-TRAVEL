"""
build_release.py - Costruisce Kotoba Travel con i dati reali.

Uso:
  python build_release.py              # auto-detect piattaforma
  python build_release.py --windows   # Flutter build (richiede Visual Studio)
  python build_release.py --linux     # Flutter build (richiede Linux)
  python build_release.py --pack      # PyInstaller exe (nessun Visual Studio)

Su Linux produce anche un AppImage portabile (richiede linuxdeploy).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DATI_REALI = ROOT / "_dati_reali"
SRC_DATA = ROOT / "src" / "asset" / "data"
SRC_FOOD = ROOT / "src" / "asset" / "image" / "food"
REAL_DATA = DATI_REALI / "data"
REAL_FOOD = DATI_REALI / "images" / "food"
BACKUP = ROOT / "_demo_backup"


def detect_platform() -> str:
    if "--pack" in sys.argv:
        return "pack"
    if "--windows" in sys.argv:
        return "windows"
    if "--linux" in sys.argv:
        return "linux"
    return "windows" if sys.platform == "win32" else "linux"


def check_prerequisites() -> None:
    if not DATI_REALI.exists():
        sys.exit("[ERRORE] _dati_reali/ non trovata.")
    if not REAL_DATA.exists():
        sys.exit("[ERRORE] _dati_reali/data/ non trovata.")
    if not REAL_FOOD.exists():
        sys.exit("[ERRORE] _dati_reali/images/food/ non trovata.")


def backup_demo() -> None:
    print("[1/4] Backup dati demo...")
    if BACKUP.exists():
        shutil.rmtree(BACKUP)
    shutil.copytree(SRC_DATA, BACKUP / "data")
    shutil.copytree(SRC_FOOD, BACKUP / "food")


def inject_real_data() -> None:
    print("[2/4] Iniezione dati reali...")
    for src in REAL_DATA.glob("*.json"):
        shutil.copy2(src, SRC_DATA / src.name)
        print(f"   {src.name}")
    food_files = [f for f in REAL_FOOD.iterdir() if f.is_file()]
    for src in food_files:
        shutil.copy2(src, SRC_FOOD / src.name)
    print(f"   {len(food_files)} foto food")


def restore_demo() -> None:
    print("[4/4] Ripristino dati demo...")
    if not BACKUP.exists():
        print("   [ATTENZIONE] Backup non trovato, skip ripristino.")
        return
    for src in (BACKUP / "data").glob("*.json"):
        shutil.copy2(src, SRC_DATA / src.name)
    for f in SRC_FOOD.iterdir():
        if f.is_file():
            f.unlink()
    for src in (BACKUP / "food").iterdir():
        if src.is_file():
            shutil.copy2(src, SRC_FOOD / src.name)
    shutil.rmtree(BACKUP)
    print("   Demo ripristinati.")


def build(platform: str) -> None:
    print(f"[3/4] flet build {platform}...")
    env = os.environ.copy()
    if platform == "windows":
        env["PYTHONUTF8"] = "1"
    result = subprocess.run(
        ["flet", "build", platform, "--module-name", "run"],
        cwd=ROOT,
        env=env,
    )
    if result.returncode != 0:
        sys.exit(f"[ERRORE] flet build fallito (exit {result.returncode})")


def find_linux_bundle() -> Path | None:
    candidates = [
        ROOT / "build" / "linux",
        ROOT / "build" / "linux" / "x64" / "release" / "bundle",
        ROOT / "build" / "linux" / "release" / "bundle",
    ]
    return next((p for p in candidates if (p / "kotoba-travel").exists() or (p / "kotoba_travel").exists()), None)


def build_appimage() -> None:
    bundle = find_linux_bundle()
    if not bundle:
        print("[ATTENZIONE] Bundle Linux non trovato, skip AppImage.")
        return

    linuxdeploy = ROOT / "linuxdeploy-x86_64.AppImage"
    plugin = ROOT / "linuxdeploy-plugin-gtk.sh"
    if not linuxdeploy.exists() or not plugin.exists():
        print("[ATTENZIONE] linuxdeploy non trovato. Esegui prima setup_linux.sh.")
        print(f"   Bundle grezzo disponibile in: {bundle}")
        return

    print("[+] Creazione AppDir...")
    appdir = ROOT / "AppDir"
    if appdir.exists():
        shutil.rmtree(appdir)

    bin_dir = appdir / "usr" / "bin"
    bin_dir.mkdir(parents=True)

    # Copia tutto il bundle in usr/bin mantenendo la struttura relativa
    for item in bundle.iterdir():
        dest = bin_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    # Rendi eseguibile il binario principale
    exe_name = "kotoba-travel" if (bin_dir / "kotoba-travel").exists() else "kotoba_travel"

    # Desktop entry
    apps_dir = appdir / "usr" / "share" / "applications"
    apps_dir.mkdir(parents=True)
    (apps_dir / "kotoba_travel.desktop").write_text(
        f"[Desktop Entry]\nName=Kotoba Travel\nExec={exe_name}\n"
        "Icon=kotoba_travel\nType=Application\nCategories=Education;\n"
    )

    # Icona
    icon_src = ROOT / "src" / "asset" / "image" / "icons" / "icona.png"
    icons_dir = appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
    icons_dir.mkdir(parents=True)
    if icon_src.exists():
        shutil.copy2(icon_src, icons_dir / "kotoba_travel.png")

    print("[+] Packaging AppImage...")
    env = os.environ.copy()
    env["DEPLOY_GTK_VERSION"] = "3"
    subprocess.run(
        [str(linuxdeploy), "--appdir", str(appdir), "--plugin", "gtk", "--output", "appimage"],
        cwd=ROOT,
        env=env,
        check=True,
    )

    candidates = [p for p in ROOT.glob("*.AppImage") if p.name != "linuxdeploy-x86_64.AppImage"]
    appimage = candidates[0] if candidates else None
    if appimage:
        print(f"\n[OK] AppImage pronto: {appimage}")
    else:
        print("\n[ATTENZIONE] AppImage non trovato - controlla l'output di linuxdeploy.")


def build_pack() -> None:
    """Exe Windows via PyInstaller — non richiede Visual Studio."""
    print("[3/4] flet pack (PyInstaller)...")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    icon = ROOT / "src" / "asset" / "image" / "icons" / "icona.ico"
    result = subprocess.run(
        [
            "flet", "pack", "run.py",
            "--name", "Kotoba Travel",
            "--icon", str(icon),
            "--add-data", "src:src",
            "-y",
        ],
        cwd=ROOT,
        env=env,
    )
    if result.returncode != 0:
        sys.exit(f"[ERRORE] flet pack fallito (exit {result.returncode})")


def find_windows_exe() -> Path | None:
    candidates = [
        ROOT / "build" / "windows" / "kotoba_travel" / "kotoba_travel.exe",
        ROOT / "build" / "windows" / "x64" / "runner" / "Release" / "kotoba_travel.exe",
    ]
    return next((p for p in candidates if p.exists()), None)


def main() -> None:
    platform = detect_platform()
    print(f"=== Kotoba Travel - Build Release ({platform}) ===\n")
    check_prerequisites()
    backup_demo()
    try:
        inject_real_data()
        if platform == "pack":
            build_pack()
        else:
            build(platform)
    finally:
        restore_demo()

    if platform == "pack":
        out = ROOT / "dist" / "Kotoba Travel.exe"
        if out.exists():
            print(f"\n[OK] Exe pronto: {out}")
        else:
            print("\n[ATTENZIONE] Exe non trovato in dist/ - controlla l'output sopra")
    elif platform == "windows":
        out = find_windows_exe()
        if out:
            print(f"\n[OK] Exe pronto: {out}")
        else:
            print("\n[ATTENZIONE] Exe non trovato - controlla la cartella build/")
    else:
        build_appimage()


if __name__ == "__main__":
    main()
