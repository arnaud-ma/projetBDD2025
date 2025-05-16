from typing import NamedTuple

import requests
from dal import autocomplete
from django.contrib import messages
from django.core.exceptions import BadRequest
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.shortcuts import render

from agence.forms import UTILISATEURS_FORMS, AgenceForm, UtilisateurForm

from .models import Adresse, Agence, Utilisateur


def index(request):
    return render(request, "agence/index.html")


# ---------------------------------------------------------------------------- #
#                                 Utilisateurs                                 #
# ---------------------------------------------------------------------------- #

class UserInfo(NamedTuple):
    id: int
    email: str
    telephone: str
    nom: str
    prenom: str
    types: str


def get_user_list():
    # Le but est d'avoir exactement la même table qui est retournée dans agence/list_users/
    # 1. On rajoute une nouvelle colonne "type_" qui vaut tout le temps "acheteur" dans
    #   la table acheteur, "vendeur" dans la table vendeur, etc.
    # 2. On fait un UNION ALL de ces tables en prenant seulement
    #   l'id utilisateur et la colonne créée
    # 3. On fait un group by sur l'id utilisateur, puis une aggrégation pour
    #    sur ces groupes qui fait l'équivalent de ",".join(type_).

    # ! ça fonctionne puisqu'on est sur sqlite, sur d'autre sgbd le ",".join()
    # peut avoir un autre nom complètement différent:

    # sqlite, mysql           -> GROUP_CONCAT
    # Oracle                  -> LISTAGG
    # SQL Server, PostrgreSQL -> STRING_AGG
    query = """
        SELECT
            utilisateur_id,
            email,
            telephone,
            nom,
            prenom,
            GROUP_CONCAT(type_ ORDER BY type_) AS types
        FROM
            agence_utilisateur
        JOIN
            (
                SELECT utilisateur_id, 'acheteur' AS type_ FROM agence_acheteur
                UNION ALL
                SELECT utilisateur_id, 'vendeur' AS type_ FROM agence_vendeur
            ) AS types_combined
            ON agence_utilisateur.id = types_combined.utilisateur_id
        GROUP BY
            utilisateur_id, email
        ORDER BY
            nom, prenom, email;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
    return [UserInfo(*ligne) for ligne in result]


def list_users(request):
    user_list = get_user_list()
    paginator = Paginator(user_list, 10)  # 10 utilisateurs par page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "agence/list_users.html", context)


def create_user_accueil(request):
    return render(
        request,
        "agence/create_user.html",
        {"accueil": True, "user_forms": UTILISATEURS_FORMS, "type_utilisateur": "utilisateur"},
    )


def create_user(request, type_utilisateur: str = "utilisateur"):
    user_form1_obj = UtilisateurForm
    user_form2_obj = UTILISATEURS_FORMS.get(type_utilisateur)
    if user_form2_obj is None:
        return BadRequest("Type d'utilisateur invalide.")

    if request.method == "POST":
        form1 = user_form1_obj(request.POST)
        form2 = user_form2_obj(request.POST)

        if form1.is_valid() and form2.is_valid():
            try:
                with transaction.atomic():
                    # Recherche si l'utilisateur existe déjà
                    utilisateur = Utilisateur.objects.filter(email=form1.cleaned_data['email']).first()
                    if utilisateur is None:
                        utilisateur = form1.save(commit=False)  # Créer un nouvel utilisateur si inexistant
                    else:
                        # Si l'utilisateur existe déjà, on met à jour le formulaire avec l'utilisateur existant
                        form1 = UtilisateurForm(instance=utilisateur)

                    # S'assurer que le type_utilisateur est bien attribué
                    utilisateur.type_utilisateur = type_utilisateur
                    utilisateur.save()

                    # Créer l'instance spécifique (par exemple, Acheteur, Vendeur) et l'associer à l'utilisateur
                    instance = form2.save(commit=False)
                    instance.utilisateur = utilisateur
                    instance.save()

                messages.success(request, "✅ Utilisateur créé avec succès !")
                return render(request, "agence/create_user.html", {"form_utilisateur": UtilisateurForm()})
            except Exception as e:
                messages.error(request, f"⚠️ Une erreur est survenue : {e!s}")
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


# ---------------------------------------------------------------------------- #
#                                    Agence                                    #
# ---------------------------------------------------------------------------- #


def create_agence(request):
    if request.method == "POST":
        form = AgenceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Agence créée avec succès !")
            return render(request, "agence/create_user.html", {"form_agence": AgenceForm()})
        else:
            messages.error(request, "⚠️ Veuillez corriger les erreurs ci-dessous.")
    else:
        form = AgenceForm()
    return render(
        request,
        "agence/create_agence.html",
        {
            "form_agence": form,
        },
    )


# ---------------------------------------------------------------------------- #
#                                   Adresses                                   #
# ---------------------------------------------------------------------------- #

class AdresseAutocomplete(autocomplete.Select2ListView):
    """Classe pour l'autocomplétion des adresses."""

    def get_list(self):
        if not self.q:
            return []
        try:
            response = requests.get(
                "https://data.geopf.fr/geocodage/completion/",
                {
                    "text": self.q,
                    "maximumResponses": 10,
                    "type": "StreetAddress",
                },
                timeout=5,
            )
            response.raise_for_status()  # Vérifie si la requête a réussi
        except (requests.RequestException, ValueError):
            return []

        result = response.json()
        if (status := result.get("status")) != "OK":
            return [f"Error status: {status}"]

        results = result.get("results")
        if not results:
            return []
        return [value for result in results if (value := result.get("fulltext"))]

    # On doit absolument surcharger cette méthode pour ne rien faire
    # puisque par défaut, Select2ListView filtre les résultats qui ne contiennent
    # pas self.q. On ne veut pas ça ici.
    def autocomplete_results(self, results):  # noqa: PLR6301
        return results
