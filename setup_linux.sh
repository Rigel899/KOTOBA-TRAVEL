#!/usr/bin/env bash
# setup_linux.sh - Prepara la VM Debian per buildare Kotoba Travel + AppImage
# Sicuro da rieseguire: ogni step controlla se è già fatto.
set -e

echo "=== [1/4] Dipendenze di sistema ==="
sudo apt-get update -qq
sudo apt-get install -y \
    python3 python3-pip python3-venv git curl wget \
    libgtk-3-dev libglib2.0-dev ninja-build cmake \
    clang pkg-config libblkid-dev liblzma-dev \
    fuse libfuse2

echo ""
echo "=== [2/4] Ambiente Python ==="
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=== [3/4] linuxdeploy per AppImage ==="
if [ ! -f "linuxdeploy-x86_64.AppImage" ]; then
    wget -q --show-progress -O linuxdeploy-x86_64.AppImage \
        "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
else
    echo "   linuxdeploy già presente, skip."
fi
if [ ! -f "linuxdeploy-plugin-gtk.sh" ]; then
    wget -q --show-progress -O linuxdeploy-plugin-gtk.sh \
        "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh"
else
    echo "   linuxdeploy-plugin-gtk già presente, skip."
fi
chmod +x linuxdeploy-x86_64.AppImage linuxdeploy-plugin-gtk.sh

echo ""
FLUTTER_BIN="$HOME/.flet/flutter/bin/flutter"
if [ -f "$FLUTTER_BIN" ]; then
    echo "=== [4/4] Flutter SDK già installato, skip. ==="
else
    echo "=== [4/4] Pre-scarico Flutter SDK (prima build, richiede tempo) ==="
    source .venv/bin/activate
    echo "y" | flet build linux --module-name run || true
fi

echo ""
echo "=== Setup completato ==="
echo "Per buildare con i dati reali:"
echo "  source .venv/bin/activate"
echo "  python build_release.py --linux"
