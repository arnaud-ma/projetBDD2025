
from django.db import models

class Vendeur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.prenom} {self.nom}"

class Acheteur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.prenom} {self.nom}"

class AgentImmobilier(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.prenom} {self.nom}"

class Bien(models.Model):
    TYPE_CHOIX = [
        ('Appartement', 'Appartement'),
        ('Maison', 'Maison'),
        ('Terrain', 'Terrain'),
    ]
    titre = models.CharField(max_length=200)
    description = models.TextField()
    adresse = models.CharField(max_length=200)
    ville = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=12, decimal_places=2)
    surface = models.FloatField()
    type_bien = models.CharField(max_length=20, choices=TYPE_CHOIX)
    vendeur = models.ForeignKey(Vendeur, on_delete=models.CASCADE, related_name='biens')

    def __str__(self):
        return self.titre

class CritereRecherche(models.Model):
    acheteur = models.ForeignKey(Acheteur, on_delete=models.CASCADE, related_name='criteres')
    ville = models.CharField(max_length=100, blank=True, null=True)
    min_prix = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    max_prix = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    type_bien = models.CharField(max_length=20, choices=Bien.TYPE_CHOIX, blank=True, null=True)
    min_surface = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"Critères de {self.acheteur}"

class Visite(models.Model):
    acheteur = models.ForeignKey(Acheteur, on_delete=models.CASCADE)
    bien = models.ForeignKey(Bien, on_delete=models.CASCADE)
    date_visite = models.DateTimeField()

    def __str__(self):
        return f"Visite de {self.acheteur} pour {self.bien}"

class Vente(models.Model):
    acheteur = models.ForeignKey(Acheteur, on_delete=models.CASCADE)
    bien = models.OneToOneField(Bien, on_delete=models.CASCADE)
    date_vente = models.DateField()
    prix_vente = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.bien} vendu à {self.acheteur}"

class RendezVous(models.Model):
    vendeur = models.ForeignKey(Vendeur, on_delete=models.CASCADE)
    agent = models.ForeignKey(AgentImmobilier, on_delete=models.CASCADE)
    date_heure = models.DateTimeField()
    sujet = models.CharField(max_length=200)

    def __str__(self):
        return f"RDV entre {self.agent} et {self.vendeur} le {self.date_heure}"
