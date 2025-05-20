from django.urls import path

from . import views
from .views import ListViewBiens, RendezVousParVendeurView, UpdateEtatBienView

urlpatterns = [
    path("", views.index, name="index"),
    # -------------------------------- Utilisateur ------------------------------- #
    # path("create_user/", views.create_user_accueil, name="create_user_accueil"),
    path("create_user/", views.CreateUserView.as_view(), name="create_user"),
    path("list_users/", views.list_users, name="list_users"),
    # ---------------------------------- Agence ---------------------------------- #
    path("create_agence/", views.create_agence, name="create_agence"),
    # ---------------------------------- Profils --------------------------------- #
    path("acheteur/<int:utilisateur_id>/", views.profil_acheteur, name="profil_acheteur"),
    # -----------------------------------Bien---------------------------------------#
    path("create_bien/", views.create_bien, name="create_bien"),
    # -----------------------------------Agent--------------------------------------#
    path("agent/<int:utilisateur_id>/", views.profil_agent, name="profil_agent"),
    # path("agent/", views.list_agents, name="list_agents"),
    # -----------------------------------LIste Bien--------------------------------------#
    path("biens/", ListViewBiens.as_view(), name="list_biens"),
    # --------------------------------RDV_vendeur----------------------------------------#
    path(
        "vendeur/<int:vendeur_id>/rendezvous/",
        RendezVousParVendeurView.as_view(),
        name="rendezvous_par_vendeur",
    ),
    # ----------------------------------- Utils ---------------------------------- #
    path("bien/<int:pk>/etat/", UpdateEtatBienView.as_view(), name="update_etat_bien"),
    path(
        "adresse-autocomplete/",
        views.AdresseAutocomplete.as_view(),
        name="adresse-autocomplete",
    ),
    path(
        "email-autocomplete/",
        views.EmailAutocomplete.as_view(),
        name="email-autocomplete",
    ),
]
