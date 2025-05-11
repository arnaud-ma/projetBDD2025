# Projet base de données 2025

## Schéma de la base de données

[lien vers drawdb](https://www.drawdb.app/editor?shareId=d45227d5d346325c65aa84d16d8766b3)

## Installation

1. Cloner le dépôt :

    ```bash
    git clone https://github.com/arnaud-ma/projetBDD2025.git
    cd projetBDD2025
    ```

2. Installer uv (si pas déjà installé).

   ### Linux ou MacOS

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

   ### Windows

    ```bash
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

3. Installer les dépendances et/ou python :

    ```bash
    uv sync
    ```

    Puis `source .venv/bin/activate` sur Linux ou MacOS, ou `.venv\Scripts\activate` sur Windows pour activer l'environnement virtuel.

4. Pour faire des commandes django(très important !!!)

    ```bash
    uv run manage.py <command>
    ```

## TODO

- [X] Formulaire pour créer un utilisateur
- [ ] Script pour peupler la base de données aléatoirement.
- [ ] formulaire pour créer une nouvelle agence (**Arnaud**)
- [ ] Adoucir la contrainte unique sur le numéro de téléphone pour inclure le null (**Arnaud**)
- [ ] ajouter création d'un agent dans formulaire pour créer utilsisateur (**Arnaud**)
- [ ] Ne plus avoir d'erreur quand un utilisateur déjà vendeur veut s'inscrire en tant qu'acheteur (**Prosper**)
- [ ] Critère de recherche pour les acheteurs (**Prosper**)
- [ ] Formulaire pour créer un bien (**Prosper**)
- [ ] Liste des biens à proximité du critère de recherche de l'acheteur (ne pas forcément exclure les biens qui correspondent pas exactement à tous les critères) (**Arnaud**)
- [ ] Suivre les biens communiqués, refusés, acceptés / retours des acheteurs / étapes d'achatt  -> via table fait_achat. Voir pour des novuelles colonnes dans fait_echat (**Arnaud**)
- [ ] Portefeuille vendeur
- [ ] Portefeuille acheteur
- [ ] Bonus...
