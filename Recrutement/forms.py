from symtable import Class

from django import forms
from weasyprint.css.validation.descriptors import descriptor

from Recrutement.models import Candidature

class FichePosteForm(forms.Form):
    CONTRAT_CHOICES = [
        ('CDI', 'CDI'),
        ('CDD', 'CDD'),
        ('Stage', 'Stage'),
        ('Alternance', 'Alternance'),
    ]

    contrat = forms.ChoiceField(choices=CONTRAT_CHOICES)
    titre_poste = forms.CharField()
    departement = forms.CharField(max_length=100)
    lieu = forms.CharField(max_length=50)
    date_fin_postulation = forms.DateField(widget=forms.DateInput(attrs={ 'type': 'date'}), input_formats=['%Y-%m-%d'])
    missions = forms.CharField(widget=forms.Textarea)
    objectifs = forms.CharField(widget=forms.Textarea)
    competences_techniques = forms.CharField(widget=forms.Textarea)
    competences_transversales = forms.CharField(widget=forms.Textarea)
    formation = forms.CharField(widget=forms.Textarea)


class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = ("nom", "prenom", "mail", "telephone", "cv")

from django import forms

class EvenementForm(forms.Form):
    summary = forms.CharField(label="Titre de l'événement", max_length=200)
    description = forms.CharField(widget=forms.Textarea, required=False)
    start_datetime = forms.DateTimeField(label="Début", widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    end_datetime = forms.DateTimeField(label="Fin", widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

