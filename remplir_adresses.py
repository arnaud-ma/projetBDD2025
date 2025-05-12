"""
Script pour remplir toutes les adresses françaises dans la base de donnée,
téléchargées depuis https://adresse.data.gouv.fr/data/ban/adresses/latest/csv.

ATTENTION: ça suppose que le base de donnée est déjà créé avec les tables
mais sans les données des adresses: tout ce qui concerne les adresses
doit être complètement vide avant de lancer ce script.
"""

import os

import django
import pandas as pd
import tqdm
from django import conf
from sqlalchemy import create_engine

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_immo.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

CHUNK_SIZE = 1_000_000


def create_url():
    db_config = conf.settings.DATABASES["default"]
    db_engine = db_config["ENGINE"]
    db_name = db_config["NAME"]
    db_user = db_config["USER"]
    db_password = db_config["PASSWORD"]
    db_host = db_config["HOST"]
    db_port = db_config["PORT"]
    if db_engine == "django.db.backends.postgresql":
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_engine == "django.db.backends.mysql":
        return f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_engine == "django.db.backends.sqlite3":
        return f"sqlite:///{db_name}"
    else:
        msg = "Unsupported database engine"
        raise ValueError(msg)


def get_df(chunksize=CHUNK_SIZE):
    return pd.read_csv(
        "adresses-france.csv",
        chunksize=chunksize,
        sep=";",
        usecols=[
            "id_fantoir",
            "rep",
            "nom_voie",
            "code_postal",
            "code_insee",
            "nom_commune",
            "lon",
            "lat",
            "alias",
            "numero",
        ],
        dtype={
            "id": "string",
            "id_fantoir": "string",
            "numero": "string",
            "rep": "string",
            "nom_voie": "string",
            "code_postal": "string",
            "code_insee": "string",
            "code_commune": "string",
            "nom_commune": "string",
            "lon": "float64",
            "lat": "float64",
            "alias": "string",
        },
    )


def get_df_communes(nb_rows, chunksize=CHUNK_SIZE):
    pbar = tqdm.tqdm(total=nb_rows, desc="Chargement des communes", unit=" lignes")

    X = pd.DataFrame()
    for chunk in get_df(chunksize=chunksize):
        x = chunk[["code_insee", "nom_commune", "code_postal"]].fillna("")
        X = pd.concat([X, x], ignore_index=True).drop_duplicates(subset=["code_insee"])
        pbar.update(len(chunk))
    X = X.rename(
        columns={
            "code_insee": "code_insee",
            "nom_commune": "nom",
            "code_postal": "code_postal",
        }
    )
    return X


def get_df_voiries(nb_lignes, chunksize=CHUNK_SIZE):
    X = pd.DataFrame()

    engine = create_engine(create_url())
    with engine.connect() as conn:
        communes_df = pd.read_sql_table(
            "agence_commune",
            conn,
            columns=["id", "code_insee"],
        )

    pbar = tqdm.tqdm(total=nb_lignes, desc="Chargement des voies", unit=" lignes")

    for chunk in get_df(chunksize=chunksize):
        df_voies = (
            chunk[["id_fantoir", "nom_voie", "code_insee"]]
            .dropna(subset=["id_fantoir"])
            .drop_duplicates(subset=["id_fantoir"])
            .merge(communes_df, on="code_insee", how="left")
            .rename(columns={"id": "commune_id", "nom_voie": "nom"})[
                ["id_fantoir", "nom", "commune_id"]
            ]
            .fillna("")
        )
        X = pd.concat([X, df_voies], ignore_index=True).drop_duplicates(subset=["id_fantoir"])
        pbar.update(len(chunk))
    return X


def save_adresses(nb_rows, chunksize=CHUNK_SIZE):
    engine = create_engine(create_url())
    with engine.connect() as conn:
        voies_df = pd.read_sql_table(
            "agence_voie",
            conn,
            columns=["id", "id_fantoir"],
        )
    pbar = tqdm.tqdm(total=nb_rows, desc="Chargement des adresses", unit=" lignes")

    for chunk in get_df(chunksize=chunksize):
        x: pd.DataFrame = (
            chunk[["id_fantoir", "numero", "rep", "alias", "lon", "lat"]]
            .dropna(subset=["id_fantoir"])
            .merge(voies_df, on="id_fantoir", how="left")
            .rename(
                columns={
                    "id": "voie_id",
                    "lon": "longitude",
                    "lat": "latitude",
                    "rep": "complement",
                }
            )[["voie_id", "numero", "complement", "alias", "longitude", "latitude"]]
            .fillna("")
        )

        with engine.connect() as conn:
            x.to_sql(
                "agence_adresse",
                conn,
                if_exists="append",
                index=False,
            )
        pbar.update(len(chunk))
        break  # Remove this line to process all chunks


def main(chunksize=CHUNK_SIZE, nb_rows: int | None = None):
    # Get the number of rows in the CSV file
    if nb_rows is None:
        with open("adresses-france.csv", encoding="utf-8") as f:
            nb_rows = sum(1 for _ in f) - 1  # -1 to exclude the header
    print(f"Total number of rows: {nb_rows}")

    # Load communes and voies dataframes
    df_communes = get_df_communes(nb_rows, chunksize)
    print("Saving communes to database...")
    with create_engine(create_url()).connect() as conn:
        df_communes.to_sql("agence_commune", conn, if_exists="append", index=False)

    df_voiries = get_df_voiries(nb_rows, chunksize)
    print("Saving voies to database...")
    with create_engine(create_url()).connect() as conn:
        df_voiries.to_sql("agence_voie", conn, if_exists="append", index=False)

    save_adresses(nb_rows, chunksize)
    print("All data saved to database.")
    print("Adresses loaded successfully.")
    # Clean up


if __name__ == "__main__":
    main(chunksize=1_000_000, nb_rows=26_054_056)
