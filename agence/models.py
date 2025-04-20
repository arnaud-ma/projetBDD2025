from django.db import models
from django.forms import CharField
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.


# ---------------------------------------------------------------------------- #
#                              region localisation                             #
# ---------------------------------------------------------------------------- #


class Lieu(models.Model):
    longitude = models.FloatField()
    latitude = models.FloatField()
    adresse = models.CharField(max_length=255, blank=True, default="")
    details = models.TextField(blank=True, default="")
    code_commune = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.adresse} ({self.code_commune}): {(self.latitude, self.longitude)})"


class Agence(models.Model):
    nom = CharField(max_length=255)
    id_lieu = models.ForeignKey(Lieu, models.CASCADE)

    def __str__(self):
        return f"{self.nom} située à {self.id_lieu}"


# endregion
# ---------------------------------------------------------------------------- #
#                                  region Bien                                 #
# ---------------------------------------------------------------------------- #


class InfosBien(models.Model):
    nb_chambres = models.IntegerField(null=True)
    nb_salles_bain = models.IntegerField(null=True)
    nb_garages = models.IntegerField(null=True)
    nb_cuisines = models.IntegerField(null=True)
    nb_wc = models.IntegerField(null=True)
    surface_habitable = models.FloatField(null=True)
    surface_terrain = models.FloatField(null=True)
    lieu = models.ForeignKey(Lieu, models.PROTECT, null=True)

    def __str__(self):
        return (
            f"InfosBien à {self.lieu}: "
            f"{self.nb_chambres} chambres, "
            f"{self.surface_habitable} m² habitable, "
            f"{self.surface_terrain} m² terrain"
        )


class Bien(models.Model):
    class Etat(models.TextChoices):
        PROSPECTION = "PR"
        ESTIMATION = "ES"
        MISE_EN_VENTE = "MV"
        SIGNATURE_COMPROMIS = "SC"
        SIGNATURE_VENTE = "SV"

    etat = models.CharField(
        max_length=2, choices=Etat.choices, default=Etat.PROSPECTION
    )
    infos_bien = models.ForeignKey(InfosBien, models.PROTECT, null=True)
    vendeur = models.ForeignKey("Vendeur", models.CASCADE)

    def __str__(self):
        attrs = {"vendeur": self.vendeur, "etat_bien": self.etat.label}
        if self.infos_bien:
            attrs["infos_bien"] = self.infos_bien
        return ", ".join(f"{k}: {v}" for k, v in attrs.items()) + f" ({self.pk})"


# endregion
# ---------------------------------------------------------------------------- #
#                              region Utilisateur                              #
# ---------------------------------------------------------------------------- #


class Utilisateur(models.Model):
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    telephone = PhoneNumberField(blank=True)
    email = models.EmailField()

    def __str__(self):
        coords = (self.email, self.telephone)
        coords = filter(None, coords)
        coords_str = ", ".join(map(str, coords))
        return f"{self.prenom} {self.nom} ({coords_str})"


class Vendeur(Utilisateur):
    pass


class Acheteur(Utilisateur):
    critere_recherche = models.ForeignKey(InfosBien, models.CASCADE, null=True)


class Agent(Utilisateur):
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
        return (
            f"Fait achat de {self.acheteur} "
            f"pour le bien {self.bien} "
            f"({self.etape_achat.label})"
        )


class RendezVous(models.Model):
    fait_achat = models.ForeignKey(FaitAchat, models.CASCADE)
    objet = models.CharField(max_length=255)
    commentaire = models.TextField(blank=True, default="")
    date = models.DateTimeField()
    lieu = models.ForeignKey(Lieu, models.PROTECT, null=True)
    agent = models.ForeignKey(Agent, models.CASCADE, null=True)

    def __str__(self):
        return f"Rendez-vous pour {self.fait_achat} ({self.date})"


class Avis(models.Model):
    fait_achat = models.ForeignKey(FaitAchat, models.CASCADE)
    commentaire = models.TextField(blank=True, default="")
    date = models.DateTimeField()

    def __str__(self):
        return f"Avis pour {self.fait_achat} ({self.date})"


# endregion
# ---------------------------------------------------------------------------- #
#                           interaction client-agent                           #
# ---------------------------------------------------------------------------- #


class AgentClient(models.Model):
    agent = models.ForeignKey(Agent, models.CASCADE)
    client = models.ForeignKey(Acheteur, models.CASCADE)

    class TypeClient(models.TextChoices):
        ACHETEUR = "A"
        VENDEUR = "V"

    type_client = models.CharField(
        max_length=1, choices=TypeClient.choices, default=TypeClient.ACHETEUR
    )

    def __str__(self):
        return f"{self.agent} - {self.client} ({self.type_client.label})"


class Message(models.Model):
    agent_client = models.ForeignKey(AgentClient, models.CASCADE)
    date = models.DateTimeField()
    message = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Message entre {self.agent_client} ({self.date})"
