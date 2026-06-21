# -*- mode: python ; coding: utf-8 -*-
"""
morphoz_snackapp.spec - Configuration PyInstaller

Générer l'exécutable :
    pyinstaller morphoz_snackapp.spec --clean --noconfirm

Note Linux : libusb-1.0-0 doit être installé sur la machine cible.
    sudo apt install libusb-1.0-0
    Règles udev pour accès imprimante sans sudo : voir docs/udev.md
"""

from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ["src/core/app.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # Ressources graphiques (icônes, images)
        ("assets", "assets"),
        # Fichiers descripteurs et icônes des modules (chargés par module_registry)
        ("src/modules", "src/modules"),
        # Modules chargés uniquement via plats_router (import dynamique non détecté
        # par l'analyse statique de PyInstaller, ex. styles_plats.py)
        ("src/utils", "src/utils"),
        # capabilities.json : chargé par escpos.capabilities via importlib_resources,
        # non inclus automatiquement par PyInstaller (pas un fichier .py)
        *collect_data_files("escpos"),
    ],
    hiddenimports=[
        # Backends libusb chargés dynamiquement par pyusb
        "usb.backend.libusb1",
        "usb.backend.libusb0",
        # Logger importé dans le bloc if __name__ == "__main__"
        "src.backend.logger",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "_tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MorphozSnackApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MorphozSnackApp",
)
