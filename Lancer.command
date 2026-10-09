#!/bin/bash
# Lance l'application Salaires (Mac) - double-cliquer dans le Finder
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python n'est pas installé / Python is not installed: https://www.python.org/downloads/"
    read -r -p "Entrée pour fermer / Press Enter to close"
    exit 1
fi
python3 -m salary_app.app
