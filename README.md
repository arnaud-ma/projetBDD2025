# Projet base de données 2025

## Schéma de la base de données

[lien vers drawdb](https://www.drawdb.app/editor?shareId=a5b369f72108dc1c10a7b253fe8c6a21)

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

4. Pour faire des commandes django

    ```bash
    uv run manage.py <command>
    ```
