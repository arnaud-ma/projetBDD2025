from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.


class Lieu(models.Model):
    longitude = models.FloatField()
    latitude = models.FloatField()
    adresse = models.CharField(max_length=255, blank=True, default="")
    details = models.TextField(blank=True, default="")
    code_commune = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.adresse} ({self.code_commune}): {(self.latitude, self.longitude)})"


class InfosBien(models.Model):
    nb_chambres = models.IntegerField(null=True)
    nb_salles_bain = models.IntegerField(null=True)
    nb_garages = models.IntegerField(null=True)
    nb_cuisines = models.IntegerField(null=True)
    nb_wc = models.IntegerField(null=True)
    surface_habitable = models.FloatField(null=True)
    surface_terrain = models.FloatField(null=True)
    id_lieu = models.ForeignKey(Lieu, models.PROTECT, null=True)

    def __str__(self):
        return (
            f"InfosBien à {self.id_lieu.adresse}, {self.id_lieu.code_commune}: "
            f"{self.nb_chambres} chambres, "
            f"{self.surface_habitable} m² habitable, "
            f"{self.surface_terrain} m² terrain"
        )


class Utilisateur(models.Model):
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    telephone = PhoneNumberField(blank=True)
    email = models.EmailField()

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.email})"


class Acheteur(models.Model):
    id_utilisateur = models.OneToOneField(Utilisateur, models.CASCADE, primary_key=True)
    id_critere_recherche = models.ForeignKey(InfosBien, models.PROTECT, null=True)

    def __str__(self):
        return f"Compte acheteur de {self.id_utilisateur}"


class Vendeur(models.Model):
    id_utilisateur = models.OneToOneField(Utilisateur, models.CASCADE, primary_key=True)

    def __str__(self):
        return f"Compte vendeur de {self.id_utilisateur}"


class Bien(models.Model):
    class EtatBien(models.TextChoices):
        PROSPECTION = "PR"
        ESTIMATION = "ES"
        MISE_EN_VENTE = "MV"
        SIGNATURE_COMPROMIS = "SC"
        SIGNATURE_VENTE = "SV"

    etat_bien = models.CharField(
        max_length=2, choices=EtatBien.choices, default=EtatBien.PROSPECTION
    )
    infos_bien = models.ForeignKey(InfosBien, models.PROTECT, null=True)
    id_vendeur = models.ForeignKey(Vendeur, models.CASCADE)

    def __str__(self):
        return (
            f"Bien à {self.infos_bien.id_lieu.adresse}, {self.infos_bien.id_lieu.code_commune}: "
            f"{self.etat_bien}, "
            f"vendeur: {self.id_vendeur}"
        )


class FaitAchat(models.Model):
    id_bien = models.ForeignKey(Bien, models.CASCADE)
    id_acheteur = models.ForeignKey(Acheteur, models.CASCADE)

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

    etape_achat = models.IntegerField(choices=EtapeAchat)

    def __str__(self):
        return (
            f"Fait achat de {self.id_acheteur.id_utilisateur} "
            f"pour le bien {self.id_bien} "
            f"({self.etape_achat})"
        )
