import datetime
import os


from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string

from RHPROJECT import settings
from .forms import FichePosteForm, CandidatureForm, EvenementForm
from .models import FichePoste, Candidature, Entretien

def index(request):
    utilisateur = request.user.username
    fiches = FichePoste.objects.exists()
    if fiches:
        context = {"username": utilisateur, 'fiches': FichePoste.objects.all().order_by('date_creation')}
    else:
        context = {"username": utilisateur, 'info': "AUCUNE FICHE DE POSTE"}
    return render(request, 'recrutement/index.html', context)

def list_poste(request):
    utilisateur = request.user.username
    fiches = FichePoste.objects.exists()
    if fiches:
        context = {"username": utilisateur, 'fiches': FichePoste.objects.all().order_by('date_creation')}
    else:
        context = {"username": utilisateur, 'info': "AUCUNE FICHE DE POSTE"}
    return render(request, 'recrutement/fiche_de_poste/list_poste.html', context)

def add_fiche_poste(request):
    utilisateur = request.user.username
    ofiche = FichePosteForm()
    context = {"form": ofiche, "username":utilisateur}
    return render(request, 'recrutement/fiche_de_poste/ajouter.html', context)

def mise_en_forme_fiche(request):
    from weasyprint import HTML

    if request.method == 'POST':
        ficheForm = FichePosteForm(request.POST)

        if ficheForm.is_valid():

            try:
                ofiche = FichePoste()
                ofiche.auteur = request.user.username
                ofiche.titre_poste = ficheForm.cleaned_data["titre_poste"]
                ofiche.date_fin_postulation = ficheForm.cleaned_data["date_fin_postulation"]
                ofiche.contrat = ficheForm.cleaned_data["contrat"]
                ofiche.departement = ficheForm.cleaned_data["departement"]
                ofiche.objectifs = ficheForm.cleaned_data["objectifs"]
                ofiche.formation = ficheForm.cleaned_data["formation"]
                ofiche.missions = ficheForm.cleaned_data["missions"]
                ofiche.competences_techniques = ficheForm.cleaned_data["competences_techniques"]
                ofiche.competences_transversales = ficheForm.cleaned_data["competences_transversales"]
                ofiche.lieu = ficheForm.cleaned_data["lieu"]
            except:
                return HttpResponse("UNE ERREUR LORS DE LA RECUPERATION")


            context = {"fiche": ofiche}


            #Génération du pdf
            try:
                html_string = render_to_string('recrutement/fiche_de_poste/mise_en_forme_fiche.html', context)
                html = HTML(string=html_string)
                pdf_file = html.write_pdf()
            except:
                return HttpResponse("UNE ERREUR LORS DE LA CONVERSION EN PDF")

            # Sauvegarde du PDF dans le modèle

            ofiche.pdf.save(f'{ofiche.titre_poste}.pdf', ContentFile(pdf_file))


            ofiche.save()

            return redirect('recrutement:detail_poste', ofiche.id)

        else:
            utilisateur = request.user.username
            context = {"form": ficheForm, "username":utilisateur}
            return render(request, 'recrutement/fiche_de_poste/ajouter.html', context)

    else:

        return redirect("recrutement:add_poste")


def publier(request, id):
    fiche = FichePoste.objects.get(id=id)
    fiche.statu = "publier"
    fiche.save()
    return redirect('recrutement:list_poste')

def depublier(request, id):
    fiche = FichePoste.objects.get(id=id)
    fiche.statu = "nonpublier"
    fiche.save()
    return redirect('recrutement:list_poste')


def fiche_poste_detail(request, pk):
    fiche_poste = get_object_or_404(FichePoste, pk=pk)
    utilisateur = request.user.username
    context = {"username": utilisateur, 'fiche': fiche_poste}
    return render(request, 'recrutement/fiche_de_poste/poste_details.html', context)

def modifier_fiche(request, pk):
    from weasyprint import HTML

    fiche = FichePoste.objects.get(id=pk)

    if request.method == 'POST':
        ficheForm = FichePosteForm(request.POST)

        if ficheForm.is_valid():



            fiche.auteur = request.user.username
            fiche.titre_poste = ficheForm.cleaned_data["titre_poste"]
            fiche.date_fin_postulation = ficheForm.cleaned_data["date_fin_postulation"]
            fiche.contrat = ficheForm.cleaned_data["contrat"]
            fiche.departement = ficheForm.cleaned_data["departement"]
            fiche.objectifs = ficheForm.cleaned_data["objectifs"]
            fiche.formation = ficheForm.cleaned_data["formation"]
            fiche.missions = ficheForm.cleaned_data["missions"]
            fiche.competences_techniques = ficheForm.cleaned_data["competences_techniques"]
            fiche.competences_transversales = ficheForm.cleaned_data["competences_transversales"]
            fiche.lieu = ficheForm.cleaned_data["lieu"]


            context = {"fiche": fiche}

            # Génération du pdf
            try:
                html_string = render_to_string('recrutement/fiche_de_poste/mise_en_forme_fiche.html', context)
                html = HTML(string=html_string)
                pdf_file = html.write_pdf()
            except:
                return HttpResponse("UNE ERREUR LORS DE LA CONVERSION EN PDF")

            # Sauvegarde du PDF dans le modèle
            try:
                fiche.pdf.save(f'{fiche.titre_poste}.pdf', ContentFile(pdf_file))

            except:
                return HttpResponse("UNE ERREUR LORS DE L'ENREGISTREMENT DU PDF ")

            fiche.save()

            return redirect('recrutement:detail_poste', pk)

        else:
            donne = FichePoste(request.POST)
            context = {"form": donne}
            return render(request, 'recrutement/fiche_de_poste/modifier.html', context)


    else:

        donne_initiale = {
            'auteur' : fiche.auteur,
            "titre_poste" : fiche.titre_poste,
            "date_fin_postulation" : fiche.date_fin_postulation,
            "contrat" : fiche.contrat,
            "departement" : fiche.departement,
            "objectifs" : fiche.objectifs,
            "formation" : fiche.formation,
            "missions" : fiche.missions,
            "competences_techniques" : fiche.competences_techniques,
            "competences_transversales" : fiche.competences_transversales,
            "lieu" : fiche.lieu

        }

        ficheForm = FichePosteForm(initial=donne_initiale)
        utilisateur = request.user.username
        context = {"form": ficheForm, "username": utilisateur, "fiche":fiche}
        return render(request, 'recrutement/fiche_de_poste/modifier.html', context)

def poste_a_publier(request):
    utilisateur = request.user.username
    fiches = FichePoste.objects.exists()
    if fiches:
        context = {"username": utilisateur, 'fiches': FichePoste.objects.filter(statu="nonpublier").order_by('date_creation')}
    else:
        context = {"username": utilisateur}
    return render(request, 'recrutement/fiche_de_poste/poste_a_publier.html', context)

def poste_a_depublier(request):
    utilisateur = request.user.username
    fiches = FichePoste.objects.exists()
    if fiches:
        context = {"username": utilisateur, 'fiches': FichePoste.objects.filter(statu="publier").order_by('date_creation')}
    else:
        context = {"username": utilisateur}
    return render(request, 'recrutement/fiche_de_poste/poste_a_depublier.html', context)

def candidatures_soumises(request):
    fiche = FichePoste.objects.all()
    utilisateur = request.user.username
    fiches = FichePoste.objects.exists()
    if fiches:
        context = {"fiches": fiche, "username":utilisateur}
    else:
        context = {"username": utilisateur}
    return render(request, 'recrutement/candidatures/list_poste_candidatures.html', context)

def candidatures_par_fiche(request, id):
    fiche = FichePoste.objects.get(id=id)
    utilisateur = request.user.username
    context = {'candidatures': Candidature.objects.filter(fiche=fiche).order_by('date_postulation'), "fiche": fiche, "username":utilisateur}
    return render(request, 'recrutement/candidatures/candidatures_par_fiche.html', context)


def candidater(request, id):
    fiche = FichePoste.objects.get(id=id)
    context = {"fiche": fiche, 'form':CandidatureForm()}
    return render(request, 'postuler.html', context)

def traiter_candidature(request):
    if request.method == "POST":
        form = CandidatureForm(request.POST, request.FILES)


        if form.is_valid():
            id = request.POST.get("fiche")
            fiche = FichePoste.objects.get(id=id)
            candidature = Candidature(cv = request.FILES["cv"],
                                      mail=request.POST["mail"],
                                      nom=request.POST["nom"],
                                      prenom=request.POST["prenom"],
                                      telephone=request.POST["telephone"],
                                      )
            candidature.fiche = fiche
            candidature.date_postulation = datetime.datetime.now()

            candidature.save()
            return render(request, "recrutement/fiche_de_poste/confirmation_postulation.html")


        else:
            context = {"form":form}
            return render(request, "postuler.html", context)



def noterCV(request,id, pk):
    candidature = Candidature.objects.get(id=id)
    if request.method == "POST":
        if request.POST:

            pertinence = request.POST.get('experience_pertinence')
            presentation_clarte = request.POST.get('presentation_clarté')
            noteCV = int(pertinence) + int(presentation_clarte)
            candidature.noteCV = noteCV

            if candidature.noteCV > 5:
                candidature.statu = Candidature.Statu.preselectioner
            else:
                candidature.statu = Candidature.Statu.en_cours

            candidature.save()
        else:
            return render(request, 'recrutement/candidatures/notationCV.html', {"id": id, "pk": pk})

        return redirect("recrutement:detailCandidature", id, pk)
    elif request.method == "GET":
        return render(request, 'recrutement/candidatures/notationCV.html', {"id":id, "pk":pk})

def noterEntretien(request,id, pk):
    candidature = Candidature.objects.get(id=id)
    if request.method == "POST":
        if request.POST:
            communication_ecoute = request.POST.get('communication_ecoute')
            communication_claire = request.POST.get('communication_claire')
            motivation_poste = request.POST.get('motivation_poste')
            motivation_entreprise = request.POST.get('motivation_entreprise')
            noteEntretien = int(communication_ecoute) + int(communication_claire) + int(motivation_poste) + int(motivation_entreprise)
            candidature.noteEntretien = noteEntretien

            if candidature.noteEntretien > 7:
                candidature.statu = Candidature.Statu.selectioner
            candidature.save()
        else:
            return render(request, 'recrutement/candidatures/notationEntretien.html', {"id": id, "pk": pk})

        return redirect("recrutement:detailCandidature", id, pk)
    elif request.method == "GET":
        return render(request, 'recrutement/entretiens/notationEntretien.html', {"id":id, "pk":pk})

def detailCandidature(request,id, pk):
    utilisateur = request.user.username
    candidature = Candidature.objects.get(id=id)
    fiche = FichePoste.objects.get(id=pk)
    context = {"candidature": candidature, "username": utilisateur, "fiche":fiche}
    return render(request, "recrutement/candidatures/detailCandidature.html", context)



def candidat_preselectionés_selon_fiche(request, id):
    fiche = FichePoste.objects.get(id=id)
    utilisateur = request.user.username
    candidats = Candidature.objects.filter(statu="preselectioner", fiche=fiche)
    context = {"candidats":candidats, "username":utilisateur, "fiche":fiche}
    return render(request, "recrutement/preselection/candidatures_preselectionés_par_fiche.html", context)

def candidat_selectionés_selon_fiche(request, id):
    fiche = FichePoste.objects.get(id=id)
    utilisateur = request.user.username
    candidats = Candidature.objects.filter(statu="selectioner", fiche=fiche)
    context = {"candidats":candidats, "username":utilisateur, "fiche":fiche}
    return render(request, "recrutement/selection/candidatures_selectionés_par_fiche.html", context)



def preselection(request):

    return render(request, "recrutement/preselection/preselection.html", {"fiches":FichePoste.objects.filter(statu="publier")})

def selection(request):
    return render(request, "recrutement/selection/selection.html", {"fiches":FichePoste.objects.filter(statu="publier")})


def sup_candidat(request, id, pk):
    candidat = Candidature.objects.get(id=id)

    if candidat.cv:
        candidatCv = os.path.join(settings.MEDIA_ROOT, candidat.cv.name)
        try:
            if os.path.exists(candidatCv):
                os.remove(candidatCv)
                candidat.delete()
        except:
            return HttpResponse(f"Erreur lors de la suppression du cv du candidat : ")
    return redirect("recrutement:candidatures", pk)


def sup_candidat_preselectionné(request, id):
    candidat = Candidature.objects.get(id=id)

    if candidat.cv:
        fichier = os.path.join(settings.MEDIA_ROOT, candidat.cv.name)
        try:
            if os.path.exists(fichier):
                os.remove(fichier)
                candidat.delete()
        except:
            return HttpResponse(f"Erreur lors de la suppression du cv du candidat : ")

    return render(request, "recrutement/preselection/candidatures_preselectionés_par_fiche.html")


def entretiens_programmés(request):
    isEntretiens = Entretien.objects.filter(statu=Entretien.Statu.scheduled).exists()
    if isEntretiens:
        return render(request, "recrutement/entretiens/programmés.html",
                      {"entretiens": Entretien.objects.filter(statu=Entretien.Statu.scheduled)})
    else:
        return render(request, "recrutement/entretiens/programmés.html", {"info": "AUCUN ENTRETIEN AU PROGRAMME"})

def entretiens_terminés(request):
    isEntretiens = Entretien.objects.filter(statu=Entretien.Statu.done).exists()
    if isEntretiens:
        return render(request, "recrutement/entretiens/terminés.html", {"entretiens": Entretien.objects.filter(statu=Entretien.Statu.done)})
    else:
        return render(request, "recrutement/entretiens/terminés.html", {"info": "AUCUN ENTRETIEN TERMINE"})



def annuler_entretien(request, id):
    entretien = Entretien.objects.get(id=id)
    entretien.delete()
    return render(request, "recrutement/entretiens/confirmation_annulation.html")


def marquer_comme_terminer(request, id):
    entretien = Entretien.objects.get(id=id)
    entretien.statu = Entretien.Statu.done
    entretien.save()
    return redirect('recrutement:entretiens_terminés')
