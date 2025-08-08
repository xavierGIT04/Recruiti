from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.urls import reverse



def seConnecter(request):
    return render(request, 'users/login.html')

def traitement_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request,user)
            if user.is_superuser:
                return redirect(reverse('admin:index'))
            elif user.groups.filter(name="Recrutement").exists():
                return redirect(reverse('recrutement:index'))


        else:
           return render(request, 'users/erreurLogin.html')
