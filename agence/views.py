# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render

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
            utilisateur = form.save()
            type_utilisateur = form.cleaned_data["type_utilisateur"]
            if type_utilisateur == "1":
                obj = Acheteur
            elif type_utilisateur == "2":
                obj = Vendeur
            else:
                raise ValueError("Invalid type_utilisateur")

            user_instance = obj.objects.create(utilisateur_ptr=utilisateur)
            user_instance.__dict__.update(utilisateur.__dict__)
            user_instance.save()
            return HttpResponse("Utilisateur créé avec succès !")
    else:
        form = UtilisateurForm()

    return render(request, "agence/create_user.html", {"form": form})