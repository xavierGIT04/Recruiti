from django.contrib import admin
from Recrutement.models import *

admin.site.register(FichePoste)
@admin.register(Entretien)
class EntretienAdmin(admin.ModelAdmin):
    list_display = (
        "summary", "candidature",
        "start_datetime", "meeting_link", "statu"   # <- statu, pas status
    )
    list_filter = ("statu", "start_datetime")       # <- statu
    search_fields = ("summary", "candidature__nom")


