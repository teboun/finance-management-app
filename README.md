# finance-management-app

## Salaires v3.1.0 — calcul des salaires (application Windows / Mac)

Programme Python (Tkinter + SQLite, aucune dépendance externe) pour :
- **tableau de bord** : employés actifs, salaires à payer et payés, primes, achats du mois, graphique des 6 derniers mois ;
- employés payés au mois, à la semaine ou à la journée ;
- retenues d'absences (taux journalier = mensuel / 30, hebdo / 6, ou taux du jour ; demi-journées acceptées) ;
- achats / avances des employés déduits du salaire ;
- primes et heures supplémentaires (+50 %, taux horaire = mensuel / 173,33 h, hebdo / 40 h, journalier / 8 h ;
  alerte au-delà de 8 h par semaine, limite légale) ;
- achats de l'entreprise ;
- calcul du net par semaine ou par mois, statut « Payé », historique des paiements
  (un nouvel enregistrement pour la même période remplace l'ancien, sans doublon) ;
- fiches de paie imprimables (une par page, ou « Enregistrer en PDF ») avec l'en-tête de l'entreprise ;
- modification de chaque ligne (cliquer sur une ligne, changer, « Enregistrer les modifications ») ;
- recherche dans chaque tableau et export Excel (.xlsx) ;
- sauvegarde / restauration des données (un fichier invalide est refusé sans toucher aux données) ;
- langue English / Français (menu à gauche, mémorisée) ; calendrier pour choisir les dates (bouton ▦) ;
- **Paramètres** : nom, adresse, téléphone et NIF de l'entreprise.

Saisie : les montants peuvent s'écrire `30000`, `30 000`, `30.000` ou `30,000` (= trente mille) et `1500,50` ;
les dates `2026-09-15` ou `15/09/2026` ; les mois `2026-09` ou `09/2026`.

### Télécharger et lancer (le plus simple)

Page **Releases** du dépôt GitHub (colonne de droite) → dernière version :

- **Windows** : télécharger `Salaires-Windows.exe` et double-cliquer. Rien à installer, pas besoin de Python.
  La première fois, si Windows affiche « Windows a protégé votre ordinateur » :
  **Informations complémentaires → Exécuter quand même** (le programme n'est pas signé numériquement).
- **Mac** (puces Apple M1 à M4) : télécharger `Salaires-Mac.zip`, décompresser, puis **clic droit sur Salaires → Ouvrir**
  la première fois.

### Données

Tout est enregistré **sur votre ordinateur** (rien n'est envoyé sur Internet) :

- programme téléchargé (`Salaires-Windows.exe` / `Salaires.app`) : `Documents/Salaires/salaires.db` ;
  mode portable : si un fichier `salaires.db` est placé à côté du programme, c'est celui-là qui est utilisé ;
- version code source (`Lancer.bat` / `Lancer.command`) : `salaires.db` dans le dossier de l'application.

L'emplacement exact est affiché dans **Paramètres** (bouton « Ouvrir le dossier »).
Utiliser le bouton **Sauvegarder** régulièrement (par exemple sur une clé USB) ; **Restaurer** recharge une sauvegarde.
Pour reprendre les données de l'ancienne version : dans le nouveau programme, **Restaurer** et choisir l'ancien `salaires.db`.

### Lancer depuis le code source (alternative)

1. Installer Python 3 depuis https://www.python.org/downloads/
   - **Windows** : cocher « Add python.exe to PATH » et laisser « tcl/tk and IDLE » coché.
   - **Mac** : utiliser l'installateur de python.org (il contient Tkinter).
2. Télécharger le code (*Code → Download ZIP*) et le décompresser.
3. **Windows** : double-cliquer sur `Lancer.bat`. **Mac** : double-cliquer sur `Lancer.command`
   (la première fois : clic droit → Ouvrir). Ou : `python -m salary_app.app` (Mac : `python3`).

### Paramètres et tests

- Paramètres (jours par mois, jour de repos, début de semaine, heures, majoration) : `salary_app/calc.py`.
- Tests : `python -m unittest discover tests` ; vérification de l'interface : `python tests/ui_check.py`.
- Construire le programme : `pip install pyinstaller pillow` puis `python build_app.py` (résultat dans `dist/`).
  Sur GitHub, la construction est automatique : pousser une étiquette `vX.Y.Z` publie une Release avec
  `Salaires-Windows.exe` et `Salaires-Mac.zip` (après tests sur Windows et Mac).
