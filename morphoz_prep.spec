# -*- mode: python ; coding: utf-8 -*-
"""
morphoz_prep.spec - Configuration PyInstaller pour le poste de préparation

Générer l'exécutable :
    pyinstaller morphoz_prep.spec --clean --noconfirm

Application allégée : pas d'impression, pas de stock, pas de carte.
Conçue pour des postes de cuisine en accès lecture seule sur les JSON partagés.
"""

a = Analysis(
    ["src/core/app_prep.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # Ressources graphiques (icônes, logos SVG)
        ("assets", "assets"),
    ],
    hiddenimports=[
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
    name="MorphozSnackApp_prep",
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
    name="MorphozSnackApp_prep",
)
