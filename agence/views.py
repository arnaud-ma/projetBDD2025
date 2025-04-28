# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return HttpResponse(
        "<p>Cette vue est une page d'accueil basique pour l'application "
        "<code>application1</code> de mon projet.</p>"
    )
