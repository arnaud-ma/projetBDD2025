# Projet base de données 2025

## Schéma de la base de données

[lien vers le schema](database_schema.svg)

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

## Peupler la base de données

Pour peupler la base de données, il y a un script pour créer des données aléatoires.

```bash
uv run manage.py peupler_data [OPTIONS]
```

Les options disponibles sont :

- `--n` : défaut à 100. Nombre indicatif sur le nombre de données à créer. Par exmeple le nombre d'utilisateurs vaut 100, le nombre d'agences est plus faible.
- `locale`: défaut à `fr_FR`. Permet de changer la locale pour générer des données dans une autre langue. Par exemple, `en_US` pour l'anglais américain.
- `--seed` : par défaut il n'y en a pas. Mettre une seed permet de générer les mêmes données à chaque fois si on utilise la même seed.

> [!WARNING]
> Les données ne sont pas forcément cohérentes entre elles, elles servent juste à tester,
> il ne faut pas y attendre plus que ça.
>
> Il est possible d'utiliser le script lorsqu'il y a déjà des données existantes, mais forcément il y a un risque d'erreurs  de conflit (unicité, etc.) si on essaye de créer des données qui existent déjà.

## TODO

- [X] Formulaire pour créer un utilisateur
- [X] Script pour peupler la base de données aléatoirement.
- [X] formulaire pour créer une nouvelle agence (**Arnaud**)
- [X] Adoucir la contrainte unique sur le numéro de téléphone pour inclure le null (**Arnaud**)
- [ ] ajouter création d'un agent dans formulaire pour créer utilsisateur (**Arnaud**)
- [X] Ne plus avoir d'erreur quand un utilisateur déjà vendeur veut s'inscrire en tant qu'acheteur (**Prosper**)
- [ ] Critère de recherche pour les acheteurs (**Prosper**)
- [ ] Formulaire pour créer un bien (**Prosper**)
- [ ] Liste des biens à proximité du critère de recherche de l'acheteur (ne pas forcément exclure les biens qui correspondent pas exactement à tous les critères) (**Arnaud**)
- [ ] Suivre les biens communiqués, refusés, acceptés / retours des acheteurs / étapes d'achatt  -> via table fait_achat. Voir pour des novuelles colonnes dans fait_echat (**Arnaud**)
- [ ] Portefeuille vendeur
- [ ] Portefeuille acheteur
- [ ] Bonus...
