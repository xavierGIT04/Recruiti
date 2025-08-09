"""
URL configuration for RHPROJECT project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from Recrutement import urls
from Users import urls
from Recrutement.models import FichePoste

def index(request):
    fiches = FichePoste.objects.exists()
    if fiches:
        context = {'fiches': FichePoste.objects.filter(statu="publier")}
    else:
        context = {'info': "AUCUNE FICHE DE POSTE"}
    return render(request, 'index.html', context)



def poste_detail(request, pk):
    fiche_poste = get_object_or_404(FichePoste, pk=pk)
    return render(request, 'poste_details.html', {'fiche': fiche_poste})



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name="index"),
    path('poste_detail/<int:pk>/', poste_detail, name="poste_detail"),

    path('users/',include("Users.urls", namespace="users")),
    path('recrutement/', include("Recrutement.urls", namespace="recrutement")),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
