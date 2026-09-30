# finance-management-app
Application web de gestion financière avec FastAPI, React et PostgreSQL.

## Calcul des salaires (application bureau)

Programme Python (Tkinter + SQLite, aucune dépendance externe) pour :
- employés payés au mois, à la semaine ou à la journée ;
- retenues d'absences (taux journalier = mensuel / 30, hebdo / 6, ou taux du jour) ;
- achats / avances des employés déduits du salaire ;
- achats de l'entreprise ;
- calcul du net par semaine ou par mois, historique des paiements.

Langue : bouton English / Français en haut à droite (mémorisé).

Lancer : `python -m salary_app.app` (les données sont dans `salaires.db`).
Tests : `python -m unittest discover tests`.
Paramètres (jours par mois, jour de repos, début de semaine) : `salary_app/calc.py`.
