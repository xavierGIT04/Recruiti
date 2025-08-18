import os
import uuid
import socket
import datetime
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from RHPROJECT import settings
from Recrutement.models import Candidature, Entretien
from Recrutement.forms import EvenementForm
from django.utils.http import urlencode

SCOPES = ['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar']
TOKEN_DIR = os.path.join(os.path.dirname(__file__), 'tokens')
CREDENTIALS_PATH = os.path.join(settings.BASE_DIR, 'JSON', 'credentials.json')


# 🔐 Initie le flow OAuth Google
def connect_google_calendar(request, id, pk):
   request.session['id'] = id
   request.session['pk'] = pk
   request.session['user_email'] = request.user.email

   redirect_uri = request.build_absolute_uri(reverse('recrutement:oauth2callback'))

   flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri=redirect_uri
   )

   authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
   )

   request.session['state'] = state
   return redirect(authorization_url)


# 🔁 Callback après autorisation Google
def oauth2callback(request, id, pk):
   state = request.session.get('state')
   user_email = request.session.get('user_email')
   id = request.session.get('id')
   pk = request.session.get('pk')

   redirect_uri = request.build_absolute_uri(reverse('recrutement:oauth2callback'))

   flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        state=state,
        redirect_uri=redirect_uri
   )

   flow.fetch_token(authorization_response=request.build_absolute_uri())
   creds = flow.credentials

   os.makedirs(TOKEN_DIR, exist_ok=True)
   token_path = os.path.join(TOKEN_DIR, f'token_{user_email}.json')

   with open(token_path, 'w') as token_file:
      token_file.write(creds.to_json())

   return redirect(reverse('recrutement:ma_vue_avec_bootstrap_modal', kwargs={'id': id, 'pk': pk}))

# 🔧 Récupère le service Google Calendar
def get_calendar_service(user_email):
   token_path = os.path.join(TOKEN_DIR, f'token_{user_email}.json')

   if not os.path.exists(token_path):
        raise Exception("Token Google introuvable.")

   creds = Credentials.from_authorized_user_file(token_path, SCOPES)

   if not creds.valid:
      if creds.expired and creds.refresh_token:
         creds.refresh(Request())
      else:
          raise Exception("Token Google invalide ou expiré.")

   return build('calendar', 'v3', credentials=creds)


# 📅 Crée un événement Google Calendar
def create_event(event, user_email):
    service = get_calendar_service(user_email)
    return service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1
    ).execute()


# 📝 Vue pour ajouter un événement
def ajouter_evenement(request, id, pk):
    utilisateur = request.user.username
    user_email = request.user.email
    candidat = get_object_or_404(Candidature, pk=id)

    if request.method == 'POST':
        form = EvenementForm(request.POST)
        if form.is_valid():
            event = {
                'summary': form.cleaned_data['summary'],
                'description': form.cleaned_data['description'],
                'start': {
                    'dateTime': form.cleaned_data['start_datetime'].isoformat(),
                    'timeZone': 'Europe/Paris'
                },
                'end': {
                    'dateTime': form.cleaned_data['end_datetime'].isoformat(),
                    'timeZone': 'Europe/Paris'
                },
                'attendees': [{'email': candidat.mail}],
                'conferenceData': {
                    'createRequest': {
                        'requestId': str(uuid.uuid4()),
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            }

            try:
                created_event = create_event(event, user_email)

                Entretien.objects.create(
                    candidature=candidat,
                    google_event_id=created_event["id"],
                    summary=event["summary"],
                    description=event["description"],
                    start_datetime=form.cleaned_data["start_datetime"],
                    end_datetime=form.cleaned_data["end_datetime"],
                    meeting_link=created_event.get("hangoutLink", ""),
                    created_by=request.user,
                    statu="scheduled"
                )

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                return redirect(reverse('recrutement:entretiens_programmés'))

            except (socket.gaierror, ConnectionError, Exception) as e:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(e)}, status=503)
                return HttpResponseBadRequest(f"Erreur : {e}")

        return render(request, 'recrutement/entretiens/ajouter.html', {'form': form, "username": utilisateur})
    else:
        form = EvenementForm()

    return render(request, 'recrutement/entretiens/ajouter.html', {'form': form, "username": utilisateur})


# 🎯 Vue pour afficher la modal Bootstrap
def ma_vue_avec_bootstrap_modal(request, id, pk):
    context = {
        'show_modal': True,
        'modal_title': "Confirmation",
        'modal_body_text': "Cliquez pour Continuer",
        'link_text': "Continuer",
        'id': id,
        'pk': pk
    }
    return render(request, 'recrutement/entretiens/popupConnection.html', context)
