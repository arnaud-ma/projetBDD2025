from typing import Final

from django.contrib import messages  # <- Ajouté
from django.core.exceptions import BadRequest
from django.http import HttpResponse
from django.shortcuts import render

from agence.forms import UTILISATEURS_FORMS, UtilisateurForm

from .models import Utilisateur


def index(request):
    return render(request, "agence/index.html")


def list_users(request):
    user_list = Utilisateur.objects.all()
    context = {
        "user_list": user_list,
    }
    return render(request, "agence/list_users.html", context)


def create_user_accueil(request):
    return render(
        request, "agence/create_user.html", {"accueil": True, "user_forms": UTILISATEURS_FORMS}
    )


def create_user(request, type_utilisateur: str):
    # UTILISATEURS_FORMS est une sorte de dictionnaire:
    # { "acheteur": AcheteurForm, "vendeur": VendeurForm, ... }
    # type_utilisateur est la clé, e.g. "acheteur"
    user_form1_obj = UtilisateurForm
    user_form2_obj = UTILISATEURS_FORMS.get(type_utilisateur)
    if user_form2_obj is None:
        return BadRequest("Type d'utilisateur invalide.")

    if request.method == "POST":
        # On fait 2 formulaires en même temps
        # 1. Formulaire Utilisateur
        # 2. Formulaire spécifique au type d'utilisateur (Acheteur, Vendeur, Agent)
        # TODO: Actuellement, si l'utilisateur existe déjà pour un compte acheteur
        # et qu'on essaie de créer un compte vendeur avec le même utilisateur
        # (cad le même email ou même téléphone) on a une erreur pusiqu'il faut respecter
        # l'unicité.
        # On voudrait qu'à la place, aucun nouvel utilisateur ne soit créé
        # et qu'on créé simplement le compte vendeur qu'on associe à l'utilisateur
        # existant. Donc presque la même chose qu'au cas actuel, mais en remplaçant
        # `utilisateur = form1.save()` par `utilisateur = filter(email=form1.email).first()`
        # la partie la plus difficile est de savoir si le formulaire 1 n'est pas valide
        # que parce qu'il y a déjà un utilisateur avec au moins un des champs qui a
        # une contrainte d'unicité (email ou téléphone mais peut être pour plus tard
        # autre champs aussi) et que cet utilisateur est utilisé par un autre
        # type d'utilisateur (acheteur, vendeur, agent)

        # TODO: utiliser des transaction pour être plus safe

        form1 = user_form1_obj(request.POST)
        form2 = user_form2_obj(request.POST)

        if form1.is_valid() and form2.is_valid():
            utilisateur = form1.save()
            instance = form2.save(commit=False)
            instance.utilisateur = utilisateur
            instance.save()
            messages.success(request, "✅ Utilisateur créé avec succès !")
            return render(request, "agence/create_user.html", {"form": UtilisateurForm()})
        else:
            messages.error(request, "⚠️ Veuillez corriger les erreurs ci-dessous.")
    else:
        form1 = user_form1_obj()
        form2 = user_form2_obj()
    return render(
        request,
        "agence/create_user.html",
        {
            "form_utilisateur": form1,
            "form_utilisateur_spec": form2,
            "type_utilisateur": type_utilisateur,
            "user_forms": UTILISATEURS_FORMS,
            "accueil": False,
        },
    )
