from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # path("create_user/", views.create_user, name="create_user"),
    path("create_user/", views.create_user_accueil, name="create_user_accueil"),
    path("create_user/<str:type_utilisateur>/", views.create_user, name="create_user"),
    path("list_users/", views.list_users, name="list_users"),
]
