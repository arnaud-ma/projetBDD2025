from django.contrib import admin

from .models import (
    Acheteur,
    Agence,
    Agent,
    Avis,
    Bien,
    FaitAchat,
    InfosBien,
    Lieu,
    Message,
    RendezVous,
    Utilisateur,
    Vendeur,
)

# Register your models here.
admin.site.register([
    Utilisateur,
    Acheteur,
    Vendeur,
    Agent,
    Lieu,
    Agence,
    InfosBien,
    Bien,
    FaitAchat,
    RendezVous,
    Avis,
    Message,
])