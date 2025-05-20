from typing import NamedTuple

import requests
from dal import autocomplete
from django.contrib import messages
from django.core.exceptions import BadRequest
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.forms import ValidationError
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .models import Bien
from django.views.generic import ListView
from .models import RendezVous, Vendeur
from agence import models
from agence.forms import (
    UTILISATEURS_FORMS,
    AgenceForm,
    TypeUtilisateurForm,
    UtilisateurForm,
    empty_utilisateur_forms,
)

from .forms import BienForm
from .models import Acheteur, Agent, FaitAchat, Utilisateur

# ---------------------------------------------------------------------------- #
#                                     Utils                                    #
# ---------------------------------------------------------------------------- #


def get_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None


# ---------------------------------------------------------------------------- #
#                                     Index                                    #
# ---------------------------------------------------------------------------- #


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
    # 4. Pour inclure les utilisateurs qui n'ont pas de type, on fait un LEFT JOIN
    #    entre la table utilisateur et le résultat de l'étape 3, et on fait un
    #    COALESCE pour remplacer les valeurs NULL par "aucune type".

    # ! ça fonctionne puisqu'on est sur sqlite, sur d'autre sgbd le ",".join()
    # peut avoir un autre nom complètement différent:

    # sqlite, mysql           -> GROUP_CONCAT
    # Oracle                  -> LISTAGG
    # SQL Server, PostrgreSQL -> STRING_AGG
    query = """
        SELECT
            agence_utilisateur.id AS utilisateur_id,
            email,
            telephone,
            nom,
            prenom,
            GROUP_CONCAT(COALESCE(type_, 'aucune type') ORDER BY type_) AS types
        FROM
            agence_utilisateur
        LEFT JOIN
            (
                SELECT utilisateur_id, 'acheteur' AS type_ FROM agence_acheteur
                UNION ALL
                SELECT utilisateur_id, 'vendeur' AS type_ FROM agence_vendeur
                UNION ALL
                SELECT utilisateur_id, 'agent' AS type_ FROM agence_agent
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
    paginator = Paginator(user_list, 100)  # 100 utilisateurs par page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "agence/list_users.html", context)


class CreateUserView(View):
    template_name = "agence/create_user.html"

    def get(self, request):
        utilisateur_form = UtilisateurForm()
        role_forms = self.init_role_forms()
        return self.render_page(request, utilisateur_form, role_forms)

    def post(self, request):
        est_utilisateur_form = "nom" in request.POST
        if est_utilisateur_form:
            return self.handle_utilisateur_submission(request)
        return self.handle_role_submission(request)

    def handle_utilisateur_submission(self, request):
        form = UtilisateurForm(request.POST)
        role_forms = self.init_role_forms()
        if form.is_valid():
            form.save(commit=True)
            messages.success(request, "✅ Utilisateur créé avec succès !")
            return redirect(request.path)
        else:
            messages.error(request, "⚠️ Veuillez corriger les erreurs.")
        return self.render_page(request, form, role_forms)

    def handle_role_submission(self, request):
        utilisateur_form = UtilisateurForm()
        role_forms = self.init_role_forms()
        submitted_form_type = request.POST.get("role", None)

        form_get = role_forms.get(submitted_form_type, None)
        if form_get is None:
            msg = f"Le type de formulaire '{submitted_form_type}' n'est pas valide."
            raise BadRequest(msg)

        form = form_get.__class__(request.POST, prefix=submitted_form_type)
        if form and form.is_valid():
            email = form.cleaned_data.get("email")
            utilisateur = get_or_none(Utilisateur, email=email)
            if utilisateur is None:
                messages.error(request, f"⚠️ Aucun utilisateur trouvé avec l'email {email}.")
                return self.render_page(request, utilisateur_form, role_forms)

            instance = form.save(commit=False)
            instance.utilisateur = utilisateur
            if submitted_form_type == "acheteur":
                instance.critere_recherche.save()
            instance.save()
            messages.success(request, f"✅ {submitted_form_type} créé avec succès !")
            return redirect(request.path)
        messages.error(request, "⚠️ Veuillez corriger les erreurs spécifiques.")
        return self.render_page(request, utilisateur_form, role_forms)

    def render_page(self, request, utilisateur_form, role_forms):
        return render(
            request,
            self.template_name,
            {
                "form_utilisateur": utilisateur_form,
                "role_forms": role_forms,
                "type_utilisateur": "utilisateur",
            },
        )

    @staticmethod
    def init_role_forms():
        return {
            label: form_class(prefix=label.lower())
            for label, form_class in UTILISATEURS_FORMS.items()
        }

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
#                                  Autocomplete                                #
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


class EmailAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        qs = Utilisateur.objects.all()
        # if not self.request.user.is_authenticated:
        #     return qs.none()
        qs = (
            qs.filter(email__contains=self.q).order_by("email").values_list("email", flat=True)[:10]
        )
        return list(map(str, qs))

    def autocomplete_results(self, results):  # noqa: PLR6301
        return results


# ---------------------------------------------------------------------------- #
#                                Profil Acheteur                               #
# ---------------------------------------------------------------------------- #

def get_proposition_biens(acheteur):
    """
    Retourne les biens qui correspondent aux critères de recherche de l'acheteur.
    """
    if not acheteur.critere_recherche:
        return []

    # On utilise les critères de recherche pour filtrer les biens
    biens = acheteur.critere_recherche.bien_set.all()
    return biens


def profil_acheteur(request, utilisateur_id):
    context: dict = {"acheteur": None, "utilisateur": None}
    utilisateur = get_or_none(Utilisateur, id=utilisateur_id)
    if utilisateur is None:
        messages.error(request, "⚠️ Utilisateur non trouvé.")
        return render(request, "agence/profil_acheteur.html", context)
    context["utilisateur"] = utilisateur

    acheteur = get_or_none(Acheteur, utilisateur=utilisateur)
    if acheteur is None:
        messages.error(request, "⚠️ Acheteur non trouvé pour cet utilisateur.")
        return render(
            request, "agence/profil_acheteur.html", {"acheteur": None, "utilisateur": utilisateur}
        )
    context["acheteur"] = acheteur
    context["faits_achat"] = FaitAchat.objects.filter(acheteur=acheteur)
    messages.success(request, "✅ Profil acheteur chargé avec succès.")
    return render(
        request,
        "agence/profil_acheteur.html",
        context,
    )

# ---------------------------------------------------#
#               BIEN                                #
# ---------------------------------------------------#


def create_bien(request):
    if request.method == "POST":
        form = BienForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/agence/")  # Ou une page de confirmation
    else:
        form = BienForm()

    return render(request, "agence/create_bien.html", {"form": form})


def profil_agent(request, utilisateur_id):
    context: dict = {"agent": None, "utilisateur": None}
    utilisateur = get_or_none(Utilisateur, id=utilisateur_id)
    if utilisateur is None:
        messages.error(request, "⚠️ Utilisateur non trouvé.")
        return render(request, "agence/profil_agent.html", context)
    context["utilisateur"] = utilisateur

    agent = get_or_none(Agent, utilisateur=utilisateur)
    if agent is None:
        messages.error(request, "⚠️ Agent non trouvé pour cet utilisateur.")
        return render(
            request, "agence/profil_agent.html", {"agent": None, "utilisateur": utilisateur}
        )
    context["agent"] = agent
    biens = models.Bien.objects.filter(agent=agent)
    context["biens"] = biens
    # fait_achats = FaitAchat.objects.filter(agent=agent).()
    messages.success(request, "✅ Profil agent chargé avec succès.")
    return render(
        request,
        "agence/profil_agent.html",
        context,
    )
class UpdateEtatBienView(UpdateView):
    model = Bien
    fields = ['etat']
    template_name = 'bien/update_etat.html'  # Ce template sera à créer

    def get_success_url(self):
        return reverse_lazy('list_biens')
    
class ListViewBiens(ListView):
    model = Bien
    template_name = "agence/list_biens.html"  # à adapter selon l'emplacement de ton template
    context_object_name = "biens"

# ---------------------------------------------------#
#            RDV_Vendeur                             #
# ---------------------------------------------------#
# views.py
from django.views.generic import ListView
from .models import RendezVous

class RendezVousParVendeurView(ListView):
    model = RendezVous
    template_name = "agence/rendezvous_vendeur.html"
    context_object_name = "rendezvous_list"

    # views.py
    def get_queryset(self):
        vendeur_id = self.kwargs["vendeur_id"]
        return RendezVous.objects.filter(fait_achat__bien__vendeur_id=vendeur_id)

