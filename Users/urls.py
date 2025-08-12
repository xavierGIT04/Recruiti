
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.seConnecter, name="connecter"),
    path('traitement_login/', views.traitement_login, name="traitement_login"),

]


