from typing import ClassVar

from django import forms
from phonenumber_field.modelfields import PhoneNumberField

from . import models


class UtilisateurForm(forms.ModelForm):
    type_utilisateur = forms.ChoiceField(
        widget=forms.Select,
        choices=[("1", "Acheteur"), ("2", "Vendeur")],
        label="Type d'utilisateur",
    )
    class Meta:
        model = models.Utilisateur
        fields: ClassVar = ["nom", "prenom", "email", "telephone"]

    
