from django.urls import path
from Recrutement import views
from Recrutement.google_calender import google_calendar_API

app_name = "recrutement"


urlpatterns = [

    path('connect-google/', google_calendar_API.connect_google_calendar, name='connect_google_calendar'),
    path('confirmation/connection', google_calendar_API.ma_vue_avec_bootstrap_modal, name='ma_vue_avec_bootstrap_modal'),
    path('entretien/<int:id>/<int:pk>/', google_calendar_API.ajouter_evenement, name='entretien'),

    path('entretien/update/annuler/<int:id>/', views.annuler_entretien, name='annuler_entretien'),
    path('entretien/update/terminer/<int:id>/', views.marquer_comme_terminer, name='marquer_comme_terminer'),

    path('entretien/programmés', views.entretiens_programmés, name='entretiens_programmés'),
    path('entretien/terminés', views.entretiens_terminés, name='entretiens_terminés'),
    path('entretien/annulés/<int:id>/', views.annuler_entretien, name='annuler_entretien'),

    path('index/', views.index, name="index" ),
    path('list_poste/', views.list_poste, name="list_poste"),
    path('add_poste/', views.add_fiche_poste, name="add_poste"),
    path("mise_en_forme/", views.mise_en_forme_fiche, name="mise_en_forme_fiche"),
    path('detail_poste/<int:pk>/', views.fiche_poste_detail, name="detail_poste"),
    path('modifier_fiche/<int:pk>/', views.modifier_fiche, name="modifier_fiche"),
    path('poste_a_publier/', views.poste_a_publier, name="poste_a_publier"),
    path('poste_a_depublier/', views.poste_a_depublier, name="poste_a_depublier"),
    path('candidatures_soumises/', views.candidatures_soumises, name="candidatures_soumises"),
    path('candidatures/<int:id>/', views.candidatures_par_fiche, name="candidatures_par_fiche"),

    path('publier/<int:id>/', views.publier, name="publier"),
    path('depublier/<int:id>/', views.depublier, name="depublier"),

    path('candidater/<int:id>/', views.candidater, name="candidater"),
    path('traiter_candidature/', views.traiter_candidature, name="traiter_candidature"),

    path('noterCV/<int:id>/<int:pk>/', views.noterCV, name="noterCV"),
    path('noterEntretien/<int:id>/<int:pk>/', views.noterEntretien, name="noterEntretien"),
    path('detailCandidature/<int:id>/<int:pk>/', views.detailCandidature, name="detailCandidature"),

    path('candidat_preselectionés/fiche/<int:id>/', views.candidat_preselectionés_selon_fiche, name="candidat_preselectionés"),

    path('candidat_selectionés/fiche/<int:id>/', views.candidat_selectionés_selon_fiche, name="candidat_selectionés"),

    path('preselections/', views.preselection, name="preselection"),

    path('selections/', views.selection, name="selection"),

    path('sup_candidat_preselectionné/candidat/<int:id>/', views.sup_candidat_preselectionné, name="sup_candidat_preselectionné"),
    path('sup_candidat/candidat/<int:id>/<int:pk>/', views.sup_candidat, name="sup_candidat"),


]
