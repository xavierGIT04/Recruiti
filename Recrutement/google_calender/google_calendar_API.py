import uuid

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path

import RHPROJECT.settings
from  Recrutement.models import *
from Recrutement.models import Candidature
from Recrutement.forms import EvenementForm

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service(user_email):
    creds = None
    token_dir = os.path.join(os.path.dirname(__file__), 'tokens')
    os.makedirs(token_dir, exist_ok=True)

    token_path = os.path.join(token_dir, f'token_{user_email}.json')
    credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service


def get_events(service):
    service = get_calendar_service()
    events = service.events().list(calendarId='primary').execute()
    return events

def create_event(event, user_email):
    service = get_calendar_service(user_email)
    created_event = service.events().insert(calendarId='primary', body=event, conferenceDataVersion=1).execute()
    print(f"Événement créé : {created_event.get('htmlLink')}")
    return created_event

from django.http import JsonResponse
import socket

def ajouter_evenement(request, id, pk):
    candidat = Candidature.objects.get(id=id)
    utilisateur = request.user.username
    user_email = request.user.email

    if request.method == 'POST':
        form = EvenementForm(request.POST)
        if form.is_valid():
            summary = form.cleaned_data['summary']
            description = form.cleaned_data['description']
            start = form.cleaned_data['start_datetime'].isoformat()
            end = form.cleaned_data['end_datetime'].isoformat()
            email = candidat.mail

            event = {
                'summary': summary,
                'description': description,
                'start': {'dateTime': start, 'timeZone': 'Europe/Paris'},
                'end': {'dateTime': end, 'timeZone': 'Europe/Paris'},
                'attendees': [{'email': email}],
                'conferenceData': {
                    'createRequest': {
                        'requestId': str(uuid.uuid4()),
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            }

            try:
                created_event = create_event(event, user_email)

                from Recrutement.models import Entretien

                Entretien.objects.create(
                    candidature=candidat,
                    google_event_id=created_event["id"],
                    summary=summary,
                    description=description,
                    start_datetime=form.cleaned_data["start_datetime"],
                    end_datetime=form.cleaned_data["end_datetime"],
                    meeting_link=created_event.get("hangoutLink", ""),
                    created_by=request.user,
                    statu="scheduled"
                )

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                return redirect('recrutement:candidat_preselectionés', pk)


            except (socket.gaierror, ConnectionError, Exception) as e:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(e)}, status=503)

        else:
            return render(request, 'recrutement/entretiens/ajouter.html', {'form': form, "username": utilisateur})
    else:
        form = EvenementForm()

    return render(request, 'recrutement/entretiens/ajouter.html', {'form': form, "username": utilisateur})


def connect_google_calendar(request):
    user_email = request.user.email
    token_dir = os.path.join(os.path.dirname(__file__), 'tokens')
    os.makedirs(token_dir, exist_ok=True)

    token_path = os.path.join(token_dir, f'token_{user_email}.json')
    credentials_path = os.path.join(RHPROJECT.settings.BASE_DIR, 'JSON', 'credentials.json')

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(token_path, 'w') as token_file:
        token_file.write(creds.to_json())

    return redirect("ma_vue_avec_bootstrap_modal")



def ma_vue_avec_bootstrap_modal(request):
    context = {
        'show_modal': True,
        'modal_title': "Confirmation",
        'modal_body_text': "Cliquez pour Continuer",
        'link_text': "Continuer"
    }
    return render(request, 'recrutement/entretiens/popupConnection.html', context)

