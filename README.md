# finance-management-app
Application web de gestion financière avec FastAPI, React et PostgreSQL.

## Calcul des salaires v3.0.1 (application bureau Windows / Mac)

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
