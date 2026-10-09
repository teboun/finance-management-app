"""Construit le programme autonome avec PyInstaller (pas besoin de Python pour l'utiliser ensuite).

    pip install pyinstaller pillow
    python build_app.py

Résultat: dist/Salaires.exe (Windows), dist/Salaires.app (Mac), dist/Salaires (Linux).
"""
import os
import sys

import PyInstaller.__main__

args = [
    "run_app.py",
    "--name", "Salaires",
    "--windowed",                      # pas de fenêtre noire de console
    "--noconfirm", "--clean",
    "--icon", os.path.join("salary_app", "assets", "icon.png"),
    "--add-data", os.pathsep.join([os.path.join("salary_app", "assets"), os.path.join("salary_app", "assets")]),
]
if sys.platform == "darwin":
    args += ["--osx-bundle-identifier", "dz.salaires.app"]
else:
    args.append("--onefile")           # un seul fichier .exe
PyInstaller.__main__.run(args)
