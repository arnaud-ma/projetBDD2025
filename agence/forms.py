from typing import ClassVar

import requests
from bidict import bidict
from dal import autocomplete
from django import forms
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import RegionalPhoneNumberWidget

from . import models

# ---------------------------------------------------------------------------- #
#                                 Utilisateurs                                 #
# ---------------------------------------------------------------------------- #

UTILISATEURS_FORMS: bidict[str, type[forms.ModelForm]] = bidict()


def enregistrer_utilisateur_form(model_name: str):
    """
    Décorateur pour enregistrer les formulaires d'utilisateur
    Le décorateur prend le nom du modèle d'utilisateur comme argument et
    enregistre le formulaire associé dans le dictionnaire UTILISATEURS_FORMS.
    Cela permet de lier facilement les formulaires à leurs labels
    """

    def decorator(form_class: type[forms.ModelForm]):
        UTILISATEURS_FORMS[model_name.lower()] = form_class
        return form_class

    return decorator


class UtilisateurForm(forms.ModelForm):
    telephone = PhoneNumberField(required=False, widget=RegionalPhoneNumberWidget())
    class Meta:
        model = models.Utilisateur
        fields: ClassVar = [
            "nom",
            "prenom",
            "email",
            "telephone",
        ]

    def clean_telephone(self):
        # Si le tel est Falsy, on renvoit None pour déclencher NULL dans la BDD
        return self.cleaned_data.get("telephone") or None


@enregistrer_utilisateur_form("Acheteur")
class AcheteurForm(forms.ModelForm):
    class Meta:
        model = models.Acheteur
        # TODO: critere_recherche
        fields: ClassVar = []
        # fields: ClassVar = ["critere_recherche"]
        # labels: ClassVar = {
        #     "critere_recherche": "Critères de recherche",
        # }


@enregistrer_utilisateur_form("Vendeur")
class VendeurForm(forms.ModelForm):
    class Meta:
        model = models.Vendeur
        fields: ClassVar = []


@enregistrer_utilisateur_form("Agent")
class AgentForm(forms.ModelForm):
    class Meta:
        model = models.Agent
        fields: ClassVar = ["agence"]
        labels: ClassVar = {
            "agence": "Agence",
        }


# ---------------------------------------------------------------------------- #
#                                    Agence                                    #
# ---------------------------------------------------------------------------- #


class AgenceForm(forms.ModelForm):
    adresse = forms.CharField(
        label="Adresse", widget=autocomplete.ListSelect2(url="adresse-autocomplete")
    )
    class Meta:
        model = models.Agence
        fields: ClassVar = ["nom", "telephone", "adresse"]
        labels: ClassVar = {
            "nom": "Nom",
            "telephone": "Téléphone",
        }
        widgets: ClassVar = {
            "telephone": RegionalPhoneNumberWidget(),
        }

    def clean_adresse(self):
        texte = self.cleaned_data["adresse"]
        try:
            adresse = models.Adresse.from_texte(texte)
        except ValueError as e:
            raise forms.ValidationError(str(e)) from e
        return adresse