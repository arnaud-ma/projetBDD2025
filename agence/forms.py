from typing import ClassVar

from bidict import bidict
from dal import autocomplete
from django import forms
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import RegionalPhoneNumberWidget

from agence.models import Agent, Utilisateur

from . import models


def get_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None


def email_autocomplete_field():
    return forms.CharField(
        label="Email", widget=autocomplete.ListSelect2(url="email-autocomplete")
    )

# ---------------------------------------------------------------------------- #
#                                     Bien                                     #
# ---------------------------------------------------------------------------- #


class InfosBienForm(forms.ModelForm):
    class Meta:
        model = models.InfosBien
        fields: ClassVar = [
            "nb_chambres",
            "nb_salles_bain",
            "nb_garages",
            "nb_cuisines",
            "nb_wc",
            "surface_habitable",
            "surface_terrain",
            "lieu",
            # "description",
            "prix",
        ]
        labels: ClassVar = {
            "nb_chambres": "Nombre de chambres",
            "nb_salles_bain": "Nombre de salles de bain",
            "nb_garages": "Nombre de garages",
            "nb_cuisines": "Nombre de cuisines",
            "nb_wc": "Nombre de WC",
            "surface_habitable": "Surface habitable (m²)",
            "surface_terrain": "Surface du terrain (m²)",
            # "description": "Description",
            "prix": "Prix (en €)",
        }
        widgets: ClassVar = {
            "lieu": autocomplete.ListSelect2(url="adresse-autocomplete"),
            "prix": forms.NumberInput(attrs={"min": 0}),
            # "description": forms.Textarea(attrs={"rows": 4}),
        }


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
        # if not hasattr(form_class, "email"):
        #     msg = f"la classe {form_class!r} doit avoir l'attribut 'email'"
        #     raise AttributeError(msg, name=None)
        UTILISATEURS_FORMS[model_name.lower()] = form_class
        return form_class

    return decorator


def empty_utilisateur_forms():
    return {lbl: form(prefix=lbl) for lbl, form in UTILISATEURS_FORMS.items()}


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


class TypeUtilisateurForm(forms.Form):
    type_utilisateur = forms.ChoiceField(
        choices=[(k, k) for k in UTILISATEURS_FORMS.keys()], label="type d'utilisateur"
    )


@enregistrer_utilisateur_form("Acheteur")
class AcheteurForm(forms.ModelForm):
    email = email_autocomplete_field()
    class Meta:
        model = models.Acheteur
        # TODO: critere_recherche
        fields: ClassVar = []

    # Tout le reste est fait pour inclure le formulaire InfosBienForm
    # dans celui-ci sans avoir rien à faire autre part, comme si c'était qu'un
    # seul formulaire

    def __init__(self, *args, **kwargs):
        data = kwargs.get("data", None)
        instance = kwargs.get("instance", None)
        self.infos_bien_instance = instance
        super().__init__(*args, **kwargs)

        self.infos_bien_form = InfosBienForm(
            data=data,
            instance=self.infos_bien_instance,
            prefix=None,  # sans prefix
        )

        # on met à jour les champs du formulaire principal avec ceux de infos_bien_form
        # puis on met à jour les valeurs initiales
        self.fields.update(self.infos_bien_form.fields)
        for name in self.infos_bien_form.fields.keys():
            self.fields[name].initial = self.infos_bien_form.initial.get(name)

    def is_valid(self):
        """
        On vérifie la validité du formulaire principal et de infos_bien_form
        """
        return super().is_valid() and self.infos_bien_form.is_valid()

    def save(self, commit=True):  # noqa: FBT002
        acheteur = super().save(commit=False)
        infos_bien_data = {
            name: self.cleaned_data[name]
            for name in self.infos_bien_form.fields.keys()
            if name in self.cleaned_data
        }

        infos_bien_form = InfosBienForm(infos_bien_data, instance=self.infos_bien_instance)
        infos_bien = infos_bien_form.save(commit=False)
        acheteur.critere_recherche = infos_bien
        if commit:
            infos_bien_form.save()
            acheteur.save()
        return acheteur


@enregistrer_utilisateur_form("Vendeur")
class VendeurForm(forms.ModelForm):
    email = email_autocomplete_field()
    class Meta:
        model = models.Vendeur
        fields: ClassVar = []


@enregistrer_utilisateur_form("Agent")
class AgentForm(forms.ModelForm):
    email = email_autocomplete_field()
    class Meta:
        model = models.Agent
        fields: ClassVar = ["agence"]
        labels: ClassVar = {
            "agence": "Agence",
        }

    def clean_email(self):
        if not Utilisateur.objects.filter(email=self.email):
            msg = "Aucun utilisateur ne possède cet email"
            raise forms.ValidationError(msg)
        if Agent.objects.filter(email=self.email):
            msg = "L'utilisateur est déjà un agent"
            raise forms.ValidationError(msg)
        return self.email

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