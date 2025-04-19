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


class Bien(models.Model):
    nb_chambres = models.IntegerField(null=True)
    nb_salles_bain = models.IntegerField(null=True)
    nb_garages = models.IntegerField(null=True)
    nb_cuisines = models.IntegerField(null=True)
    nb_wc = models.IntegerField(null=True)
    surface_habitable = models.FloatField(null=True)
    surface_terrain = models.FloatField(null=True)
    id_lieu = models.ForeignKey(Lieu, on_delete=models.PROTECT, null=True)


class Utilisateur(models.Model):
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    telephone = PhoneNumberField(blank=True)
    email = models.EmailField()