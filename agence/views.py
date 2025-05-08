from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages  # <- Ajouté

from agence.forms import UtilisateurForm
from .models import Acheteur, Utilisateur, Vendeur

def index(request):
    return render(request, "agence/index.html")

def list_users(request):
    user_list = Utilisateur.objects.all()
    context = {
        "user_list": user_list,
    }
    return render(request, "agence/list_users.html", context)

def create_user(request):
    if request.method == "POST":
        form = UtilisateurForm(request.POST)
        if form.is_valid():
            utilisateur = form.save(commit=False)
            type_utilisateur = form.cleaned_data["type_utilisateur"]
            if type_utilisateur == "1":
                user_instance = Acheteur()
            elif type_utilisateur == "2":
                user_instance = Vendeur()
            else:
                messages.error(request, "Type d'utilisateur invalide.")
                return render(request, "agence/create_user.html", {"form": form})

            user_instance.nom = utilisateur.nom
            user_instance.prenom = utilisateur.prenom
            user_instance.email = utilisateur.email
            user_instance.telephone = utilisateur.telephone
            user_instance.type_utilisateur = type_utilisateur
            user_instance.save()

            messages.success(request, "✅ Utilisateur créé avec succès !")
            return render(request, "agence/create_user.html", {"form": UtilisateurForm()})
        else:
            messages.error(request, "⚠️ Veuillez corriger les erreurs ci-dessous.")
    else:
        form = UtilisateurForm()

    return render(request, "agence/create_user.html", {"form": form})
