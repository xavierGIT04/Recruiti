import os
import base64
import google.auth.transport.requests
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings

SCOPES = ['https://www.googleapis.com/auth/calendar.events']
CLIENT_SECRETS_FILE = os.path.join(settings.BASE_DIR, 'credentials.json')

def encode_state(id, pk):
    raw = f"{id}:{pk}"
    return base64.urlsafe_b64encode(raw.encode()).decode()

def decode_state(state):
    try:
        raw = base64.urlsafe_b64decode(state.encode()).decode()
        id, pk = raw.split(":")
        return id, pk
    except Exception:
        return None, None

def connect_google_calendar(request, id , pk):
    id = request.GET.get('id')
    pk = request.GET.get('pk')

    if not id or not pk:
        return HttpResponse("Paramètres manquants")

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri='https://recruiti.onrender.com/recrutement/oauth2callback/'
    )

    state = encode_state(id, pk)
    flow.params['access_type'] = 'offline'
    flow.params['include_granted_scopes'] = 'true'

    authorization_url, _ = flow.authorization_url(state=state)
    return redirect(authorization_url)

def oauth2callback(request):
    state = request.GET.get('state')
    code = request.GET.get('code')

    id, pk = decode_state(state)
    if not id or not pk:
        return HttpResponse("Échec du décodage du state")

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri='https://recruiti.onrender.com/recrutement/oauth2callback/'
    )
    flow.fetch_token(code=code)

    credentials = flow.credentials
    service = build('calendar', 'v3', credentials=credentials)

    event = {
        'summary': 'Entretien recruteur',
        'location': 'En ligne',
        'description': 'Entretien via Google Meet',
        'start': {
            'dateTime': '2025-08-18T10:00:00+00:00',
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': '2025-08-18T11:00:00+00:00',
            'timeZone': 'UTC',
        },
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()

    # ✅ Redirection vers la popup avec les bons paramètres
    return redirect('recrutement:ma_vue_avec_bootstrap_modal', id, pk)


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
