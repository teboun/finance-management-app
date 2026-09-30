# finance-management-app
Application web de gestion financière avec FastAPI, React et PostgreSQL.

## Calcul des salaires v2.0 (application bureau Windows / Mac)

Programme Python (Tkinter + SQLite, aucune dépendance externe) pour :
- employés payés au mois, à la semaine ou à la journée ;
- retenues d'absences (taux journalier = mensuel / 30, hebdo / 6, ou taux du jour) ;
- achats / avances des employés déduits du salaire ;
- primes et heures supplémentaires (+50 %, taux horaire = mensuel / 173,33 h, hebdo / 40 h, journalier / 8 h) ;
- achats de l'entreprise ;
- calcul du net par semaine ou par mois, historique des paiements ;
- fiche de paie imprimable (ou « Enregistrer en PDF ») ;
- export Excel (.xlsx) de chaque liste ;
- sauvegarde / restauration des données ;
- langue English / Français (bouton en haut à droite, mémorisé).

### Installation

1. Installer Python 3 depuis https://www.python.org/downloads/
   - **Windows** : cocher « Add python.exe to PATH » et laisser « tcl/tk and IDLE » coché.
   - **Mac** : utiliser l'installateur de python.org (il contient Tkinter).
2. Télécharger ce dossier (bouton *Code → Download ZIP* sur GitHub, branche `claude/funny-ptolemy-qrcr3h`) et le décompresser.

### Lancer

- **Windows** : double-cliquer sur `Lancer.bat`.
- **Mac** : double-cliquer sur `Lancer.command` (la première fois : clic droit → Ouvrir).
- Ou en ligne de commande, dans le dossier : `python -m salary_app.app` (Mac : `python3`).

### Données

Tout est enregistré **sur votre ordinateur**, dans le fichier `salaires.db` du dossier (rien n'est envoyé sur Internet).
Utiliser le bouton **Sauvegarder** régulièrement (par exemple sur une clé USB) ; **Restaurer** recharge une sauvegarde.
Pour mettre à jour l'application, garder `salaires.db` et remplacer les autres fichiers.

### Paramètres et tests

- Paramètres (jours par mois, jour de repos, début de semaine, heures, majoration) : `salary_app/calc.py`.
- Tests : `python -m unittest discover tests`.
