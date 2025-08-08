from django.db import models
from django.urls import reverse
from docutils.nodes import status
import uuid
from django.conf import settings
from django.utils import timezone



# Create your models here.


class FichePoste(models.Model):

    class Statu(models.TextChoices):
        publier = "publier"
        nonpublier = "nonpublier"

    auteur = models.CharField(max_length=100)
    statu = models.fields.CharField(choices=Statu.choices, default="nonpublier", max_length=15)
    date_creation = models.DateField(auto_now_add=True)
    titre_poste = models.CharField( max_length=50)
    departement = models.CharField(max_length=100)
    lieu = models.CharField(max_length=50)
    contrat = models.CharField(max_length=10)
    date_fin_postulation = models.DateField()
    missions = models.TextField()
    objectifs = models.TextField()
    competences_techniques = models.TextField()
    competences_transversales = models.TextField()
    formation = models.TextField()
    pdf = models.FileField(upload_to='fiche_poste/', null=True, blank=True)

    def __str__(self):
        return f"{self.titre_poste}-{self.auteur}-{self.date_creation}"

    def get_absolute_url(self):
        return reverse('recrutement/fiche_de_poste/poste_details.html', args=[str(self.id)])

    @property
    def nbreCandidatures(self):
        return self.candidature_set.count()

    @property
    def nbrePreselectioner(self):
        return self.candidature_set.filter(statu=Candidature.Statu.preselectioner).count()

    @property
    def nbreSelectioner(self):
        return self.candidature_set.filter(statu=Candidature.Statu.selectioner).count()




class Candidature(models.Model):

    class Statu(models.TextChoices):
        preselectioner = "preselectioner"
        selectioner = "selectioner"
        en_cours = "none"

    statu = models.fields.CharField(choices=Statu.choices, default=Statu.en_cours, max_length=15)
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    mail = models.EmailField()
    telephone = models.CharField(max_length=10)
    date_postulation = models.DateField()
    cv = models.FileField(upload_to="candidatures/", null=False, blank=False)
    fiche = models.ForeignKey(FichePoste, on_delete=models.CASCADE)
    noteCV = models.IntegerField(null=True, default=0)
    noteEntretien = models.IntegerField(null=True, default=0)

class Entretien(models.Model):
    class Statu(models.TextChoices):
        scheduled = "scheduled", "Programmé"
        done = "done", "Terminé"

    candidature = models.ForeignKey("Candidature", on_delete=models.CASCADE, related_name="entretiens")
    google_event_id = models.CharField(max_length=255, unique=True)
    summary = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    meeting_link = models.URLField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name="entretiens_crees")
    statu = models.CharField(max_length=15, choices=Statu.choices, default=Statu.scheduled)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_past(self):
        return self.end_datetime < timezone.now()

    def __str__(self):
        return f"{self.summary} - {self.candidature.nom} ({self.start_datetime})"


