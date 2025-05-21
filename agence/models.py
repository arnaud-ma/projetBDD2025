from math import atan2, cos, radians, sin, sqrt
from typing import ClassVar

import requests
from bidict import bidict
from django.db import models, transaction
from djmoney.models.fields import MoneyField
from phonenumber_field.modelfields import PhoneNumberField
from sklearn.metrics.pairwise import cosine_similarity

# Create your models here.

# ---------------------------------------------------------------------------- #
#                              region localisation                             #
# ---------------------------------------------------------------------------- #


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcule la distance entre deux points géographiques en utilisant la formule de Haversine.
    :param lat1: Latitude du premier point
    :param lon1: Longitude du premier point
    :param lat2: Latitude du deuxième point
    :param lon2: Longitude du deuxième point
    :return: Distance en kilomètres
    """

    R = 6371.0  # Rayon de la Terre en kilomètres

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


class Commune(models.Model):
    code_insee = models.CharField(max_length=5, unique=True)
    nom = models.CharField(max_length=255)
    code_postal = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.nom} ({self.code_postal})"


class Voie(models.Model):
    nom = models.CharField(max_length=255)
    commune = models.ForeignKey(Commune, models.PROTECT)

    class Meta:
        unique_together: ClassVar = [("nom", "commune")]

    def __str__(self):
        return f"{self.nom} - {self.commune}"


class Adresse(models.Model):
    id_ban = models.CharField(max_length=64, unique=True)
    voie = models.ForeignKey(Voie, models.PROTECT)
    numero = models.CharField(max_length=10, blank=True)
    complement = models.CharField(max_length=10, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    label = models.CharField(max_length=255)

    def __str__(self):
        return self.label

    @classmethod
    def from_texte(cls, texte: str) -> "Adresse":
        texte = texte.strip()

        # ! toute la doc est ici:
        # https://adresse.data.gouv.fr/outils/api-doc/adresse
        try:
            response = requests.get(
                "https://api-adresse.data.gouv.fr/search/",
                {"q": texte, "limit": 1, "autocomplete": 0},
                timeout=5,
            )
            response.raise_for_status()
            result = response.json()
        except (requests.RequestException, ValueError) as e:
            msg = "Adresse introuvable ou API inaccessible"
            raise ValueError(msg) from e
        try:
            result = result["features"][0]
            longitude, latitude = result["geometry"]["coordinates"]
            prop = result["properties"]
            commune_insee = prop["citycode"]
            commune = prop["city"]
            code_postal = prop["postcode"]

            voie = prop["street"]

            id_ban = prop["id"]
            numero = prop.get("housenumber", "")
            label = prop["label"]

        except (KeyError, TypeError, ValueError) as e:
            msg = "Réponse API invalide"
            raise ValueError(msg) from e

        # On vérifie si l'adresse existe déjà dans la BDD
        if Adresse.objects.filter(id_ban=id_ban).exists():
            return Adresse.objects.get(id_ban=id_ban)

        # On encapsule la création de l'adresse dans une transaction
        # pour garantir l'intégrité des données
        with transaction.atomic():
            commune, _ = Commune.objects.get_or_create(
                code_insee=commune_insee, nom=commune, code_postal=code_postal
            )
            voie, _ = Voie.objects.get_or_create(nom=voie, commune=commune)
            adresse, _ = cls.objects.get_or_create(
                id_ban=id_ban,
                voie=voie,
                numero=numero,
                complement="",  # TODO: à changer
                longitude=longitude,
                latitude=latitude,
                label=label,
            )
        return adresse

    def create_label(self, *, only_if_not_exists=True, save=False) -> str:
        """
        Renvoie le label de l'adresse, le crée si il n'existe pas déjà.

        :param only_if_not_exists: Si True et que le label existe déjà, renvoie
            seulement le label existant.
        :param save: Si True et que le label est créé, enregistre l'adresse dans la BDD.
        :return: Le label de l'adresse.
        """

        if only_if_not_exists and self.label:
            return self.label

        parts = [self.numero, self.voie.nom]
        if self.complement:
            parts.append(self.complement)
        parts.append(self.voie.commune.nom)
        label = ", ".join(filter(None, parts))
        if save:
            with transaction.atomic():
                self.label = label
                self.save(update_fields=["label"])
        return label


class Agence(models.Model):
    nom = models.CharField(max_length=255)
    adresse = models.ForeignKey(Adresse, models.PROTECT)
    telephone = PhoneNumberField(null=True, blank=True, unique=True, default=None)

    def __str__(self):
        return f"{self.nom}"


# endregion
# ---------------------------------------------------------------------------- #
#                                  region Bien                                 #
# ---------------------------------------------------------------------------- #


class InfosBien(models.Model):
    nb_chambres = models.IntegerField(null=True, blank=True)
    nb_salles_bain = models.IntegerField(null=True, blank=True)
    nb_garages = models.IntegerField(null=True, blank=True)
    nb_cuisines = models.IntegerField(null=True, blank=True)
    nb_wc = models.IntegerField(null=True, blank=True)
    surface_habitable = models.FloatField(null=True, blank=True)
    surface_terrain = models.FloatField(null=True, blank=True)
    lieu = models.ForeignKey(Adresse, models.PROTECT, null=True, blank=True)
    description = models.TextField(blank=True, default="")
    prix = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="EUR",  # type: ignore
        blank=True,
        null=True,
    )

    def __str__(self):
        return (
            f"InfosBien à {self.lieu}: "
            f"{self.nb_chambres} chambres, "
            f"{self.surface_habitable} m² habitable, "
            f"{self.surface_terrain} m² terrain"
        )

    def distance(self, autre: "InfosBien") -> float:
        """
        Calcule la distance entre deux biens en utilisant la distance de Haversine.
        :param autre: L'autre bien.
        :return: La distance en kilomètres.
        """
        return haversine_distance(
            self.lieu.latitude,
            self.lieu.longitude,
            autre.lieu.latitude,
            autre.lieu.longitude,
        )

    def score_correspondance(self, autre: "InfosBien") -> int:
        """
        Renvoie un score de correspondance entre le bien et les critères de recherche.
        Plus le score est élevé, plus le bien correspond aux critères.

        :param critere_recherche: Les critères de recherche.
        :return: Le score de correspondance.
        """
        # On crée un vecteur de caractéristiques pour le bien
        # et un autre pour les critères de recherche
        bien_vector = [
            self.nb_chambres,
            self.nb_salles_bain,
            self.nb_garages,
            self.nb_cuisines,
            self.nb_wc,
            self.surface_habitable,
            self.surface_terrain,
        ]
        critere_vector = [
            autre.nb_chambres,
            autre.nb_salles_bain,
            autre.nb_garages,
            autre.nb_cuisines,
            autre.nb_wc,
            autre.surface_habitable,
            autre.surface_terrain,
        ]

        dist = self.distance(autre=autre)

        # On calcule la similarité cosinus entre les deux vecteurs
        score = cosine_similarity([bien_vector], [critere_vector])[0][0]
        return int(score * 100) - int(dist / 1000)


class Bien(models.Model):
    class Etat(models.TextChoices):
        PROSPECTION = "PR"
        ESTIMATION = "ES"
        MISE_EN_VENTE = "MV"
        SIGNATURE_COMPROMIS = "SC"
        SIGNATURE_VENTE = "SV"

    etat = models.CharField(max_length=2, choices=Etat.choices, default=Etat.PROSPECTION)
    infos_bien = models.ForeignKey(InfosBien, models.PROTECT, null=True)
    vendeur = models.ForeignKey("Vendeur", models.CASCADE)
    agent = models.ForeignKey("Agent", models.CASCADE, null=True)  # TODO: remove null=True

    def __str__(self):
        # get_etat_display() est une méthode de Django qui renvoie le nom lisible de l'état
        attrs = {"vendeur": self.vendeur, "etat_bien": self.get_etat_display()}
        if self.infos_bien:
            attrs["infos_bien"] = self.infos_bien
        return ", ".join(f"{k}: {v}" for k, v in attrs.items()) + f" ({self.pk})"


# endregion
# ---------------------------------------------------------------------------- #
#                              region Utilisateur                              #
# ---------------------------------------------------------------------------- #

# L'idée est d'avoir une table commune Utilisateur
# et ensuite un utilisateur peut être un Acheteur, un Vendeur, etc...
# donc l'identifiant de l'utilisateur est la clé primaire de la table Utilisateur
# et c'est en même temps une clé primaire et étrangère "one-to-one" dans les "sous-tables".

# Pour simplifier la gestion des utilisateurs, on utilise un proxy
# cad une classe parente dont les sous-tables héritent
# et qui se charge de tout ce qui est commun à tous les utilisateurs


class Utilisateur(models.Model):
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    telephone = PhoneNumberField(null=True, blank=True, unique=True, default=None)
    email = models.EmailField(unique=True)

    def __str__(self):
        coords = (self.email, self.telephone)  # récupérer les coordonnées
        coords = filter(None, coords)  # filtrer les coordonnées vides
        coords_str = ", ".join(map(str, coords))  # convertir en chaîne
        if coords_str:
            # s'il existe au moins une coordonnée, ajouter des parenthèses
            coords_str = f" ({coords_str})"

        return f"{self.prenom} {self.nom} {coords_str}"


class ProxyUtilisateur:
    """Classe proxy pour Utilisateur."""

    TYPE_UTILISATEURS: ClassVar[bidict[str, type["ProxyUtilisateur"]]] = bidict()

    def __init_subclass__(cls, *args, name=None, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        # On enregistre la classe dans le dict
        if name is None:
            name = cls.__name__.lower()
        if cls is not ProxyUtilisateur and cls not in ProxyUtilisateur.TYPE_UTILISATEURS:
            ProxyUtilisateur.TYPE_UTILISATEURS[cls.__name__.lower()] = cls

    def __str__(self):
        coords = (self.utilisateur.email, self.utilisateur.telephone)  # récupérer les coordonnées
        coords = filter(None, coords)  # filtrer les coordonnées vides
        coords_str = ", ".join(map(str, coords))  # convertir en chaîne
        if coords_str:
            # s'il existe au moins une coordonnée, ajouter des parenthèses
            coords_str = f"({coords_str})"

        return f"{self.utilisateur.prenom} {self.utilisateur.nom} {coords_str}"

    @classmethod
    def url_cls(cls, id_):
        class_name = cls.__name__.lower()
        return f"/agence/{class_name}/{id_}/"

    def url(self):
        return self.url_cls(self.utilisateur.id)

    @classmethod
    def url_html_cls(cls, id_):
        return f'<a href="{cls.url_cls(id_)}">{cls.__name__.lower()}</a>'

    def url_html(self):
        return f'<a href="{self.url()}">{self.__class__.__name__.lower()}</a>'


class Vendeur(ProxyUtilisateur, models.Model):
    utilisateur = models.OneToOneField(Utilisateur, models.CASCADE, primary_key=True)


class Acheteur(ProxyUtilisateur, models.Model):
    utilisateur = models.OneToOneField(Utilisateur, models.CASCADE, primary_key=True)

    critere_recherche = models.ForeignKey(InfosBien, models.CASCADE, null=True)


class Agent(ProxyUtilisateur, models.Model):
    utilisateur = models.OneToOneField(Utilisateur, models.CASCADE, primary_key=True)
    agence = models.ForeignKey(Agence, models.CASCADE)

    def __str__(self):
        return f"{super().__str__()}, agence: {self.agence}"


# endregion
# ---------------------------------------------------------------------------- #
#                      region Interaction acheteur - bien                      #
# ---------------------------------------------------------------------------- #


class FaitAchat(models.Model):
    bien = models.ForeignKey(Bien, models.CASCADE)
    acheteur = models.ForeignKey(Acheteur, models.CASCADE)

    class EtapeAchat(models.IntegerChoices):
        PROSPECTION = 1
        PROPOSITION = 2
        VISITE = 3
        INTERET = 4
        OFFRE = 5
        NEGOCIATION = 6
        COMPROMIS_SIGNE = 7, "Compromis Signé"
        FINANCEMENT = 8
        ACTE_SIGNE = 9, "Acte Signé"
        REFUSE = 10, "Refusé"
        ABANDON = 11

    etape_achat = models.IntegerField(choices=EtapeAchat.choices)

    def __str__(self):
        return f"Fait achat de {self.acheteur} pour le bien {self.bien} ({self.etape_achat})"


class RendezVous(models.Model):
    fait_achat = models.ForeignKey(FaitAchat, models.CASCADE)
    objet = models.CharField(max_length=255)
    commentaire = models.TextField(blank=True, default="")
    date = models.DateTimeField()
    lieu = models.ForeignKey(Adresse, models.PROTECT, null=True)

    def __str__(self):
        return f"Rendez-vous pour {self.fait_achat} ({self.date})"


class Avis(models.Model):
    fait_achat = models.ForeignKey(FaitAchat, models.CASCADE)
    commentaire = models.TextField(blank=True, default="")
    date = models.DateTimeField()

    def __str__(self):
        return f"Avis pour {self.fait_achat} ({self.date})"


class Message(models.Model):
    date = models.DateTimeField()
    contenu = models.TextField(blank=True, default="")
    auteur = models.ForeignKey(Utilisateur, models.CASCADE)
    fait_achat = models.ForeignKey(FaitAchat, models.CASCADE)

    def __str__(self):
        return f"Message de {self.auteur} pour {self.fait_achat} ({self.date})"


# endregion
