from django.contrib import admin

from .models import (
    Acheteur,
    Adresse,
    Agence,
    Agent,
    Avis,
    Bien,
    Commune,
    FaitAchat,
    InfosBien,
    Message,
    RendezVous,
    Utilisateur,
    Vendeur,
    Voie,
)

# Register your models here.
admin.site.register(
    [
        Utilisateur,
        Acheteur,
        Vendeur,
        Agent,
        Agence,
        InfosBien,
        Bien,
        FaitAchat,
        RendezVous,
        Avis,
        Message,
        Adresse,
        Commune,
        Voie,
    ]
)
