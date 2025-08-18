import os
import uuid
import socket

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from RHPROJECT import settings
from Recrutement.models import Candidature, Entretien
from Recrutement.forms import EvenementForm

SCOPES = ['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar']


# 🔐 Connexion à Google Calendar (initie le flow OAuth)
def connect_google_calendar(request, id, pk):
    user_email = request.user.email
    request.session['user_email'] = user_email
    request.session['id'] = id
    request.session['pk'] = pk

    credentials_path = os.path.join(settings.BASE_DIR, 'JSON', 'credentials.json')

    flow = Flow.from_client_secrets_file(
        credentials_path,
        scopes=SCOPES,
        redirect_uri=request.build_absolute_uri('/recrutement/oauth2callback/')
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    request.session['state'] = state
    return redirect(authorization_url)


# 🔁 Callback après autorisation Google
def oauth2callback(request):
    state = request.session.get('state')
    user_email = request.session.get('user_email')
    id = request.session.get('id')
    pk = request.session.get('pk')

    credentials_path = os.path.join(settings.BASE_DIR, 'JSON', 'credentials.json')

    flow = Flow.from_client_secrets_file(
        credentials_path,
        scopes=SCOPES,
        state=state,
        redirect_uri=request.build_absolute_uri('/recrutement/oauth2callback/')
    )

    flow.fetch_token(authorization_response=request.build_absolute_uri())
    creds = flow.credentials

    token_dir = os.path.join(os.path.dirname(__file__), 'tokens')
    os.makedirs(token_dir, exist_ok=True)
    token_path = os.path.join(token_dir, f'token_{user_email}.json')

    with open(token_path, 'w') as token_file:
        token_file.write(creds.to_json())

    return redirect("recrutement:ma_vue_avec_bootstrap_modal", id=id, pk=pk)


# 🔧 Récupère le service Google Calendar
def get_calendar_service(user_email):
    token_dir = os.path.join(os.path.dirname(__file__), 'tokens')
    token_path = os.path.join(token_dir, f'token_{user_email}.json')

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Utilisateur non authentifié avec Google Calendar.")

    return build('calendar', 'v3', credentials=creds)


# 📅 Crée un événement Google Calendar
def create_event(event, user_email):
    service = get_calendar_service(user_email)
    created_event = service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1
    ).execute()

    print(f"Événement créé : {created_event.get('htmlLink')}")
    return created_event


# 📝 Vue pour ajouter un événement via formulaire
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


# 🎯 Vue pour afficher la modal Bootstrap après connexion
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
