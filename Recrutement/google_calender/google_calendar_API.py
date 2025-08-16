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
    """
    Initialise le flux d'autorisation Google sans utiliser la session pour id et pk.
    Ces variables sont encodées dans le paramètre `state`.
    """
    user_email = request.user.email

    credentials_path = os.path.join(settings.BASE_DIR, 'JSON', 'credentials.json')

    # Encodage des paramètres id et pk dans le paramètre `state`
    # Cela permet de les récupérer plus tard sans dépendre de la session
    state_data = {
        'id': id,
        'pk': pk,
        'email': user_email,
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    flow = Flow.from_client_secrets_file(
        credentials_path,
        scopes=SCOPES,
        redirect_uri=request.build_absolute_uri('/recrutement/oauth2callback/')
    )

    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=encoded_state # Utilisation du paramètre d'état encodé
    )

    return redirect(authorization_url)

# 🔁 Callback après autorisation Google
def oauth2callback(request):
    """
    Vue de rappel pour l'autorisation Google.
    Elle décode les paramètres id et pk du paramètre `state`.
    """
    # Vérifie si le paramètre `state` est présent dans la requête
    if 'state' not in request.GET:
        # Gérer l'erreur si le paramètre `state` est manquant
        return redirect('recrutement:page_erreur') 

    # Décodage de la chaîne `state` pour récupérer les paramètres
    encoded_state = request.GET.get('state')
    state_data = json.loads(base64.urlsafe_b64decode(encoded_state.encode()).decode())

    # Récupération des paramètres sans utiliser la session
    id = state_data.get('id')
    pk = state_data.get('pk')
    user_email = state_data.get('email')

    credentials_path = os.path.join(settings.BASE_DIR, 'JSON', 'credentials.json')

    flow = Flow.from_client_secrets_file(
        credentials_path,
        scopes=SCOPES,
        redirect_uri=request.build_absolute_uri('/recrutement/oauth2callback/')
    )

    try:
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        creds = flow.credentials

        token_dir = os.path.join(os.path.dirname(__file__), 'tokens')
        os.makedirs(token_dir, exist_ok=True)
        token_path = os.path.join(token_dir, f'token_{user_email}.json')

        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())

        # Redirection finale avec les paramètres récupérés
        return redirect("recrutement:ma_vue_avec_bootstrap_modal", id=id, pk=pk)
    
    except Exception as e:
        # Gérer les erreurs de connexion ou de token
        print(f"Erreur d'authentification: {e}")
        return redirect('recrutement:page_erreur_de_connexion')


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
            start_datetime = form.cleaned_data['start_datetime']
            end_datetime = form.cleaned_data['end_datetime']
            email = candidat.mail

            event = {
                'summary': summary,
                'description': description,
                'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'Europe/Paris'},
                'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'Europe/Paris'},
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
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    meeting_link=created_event.get("hangoutLink", ""),
                    created_by=request.user,
                    statu="scheduled"
                )

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Entretien créé avec succès!'})
                else:
                    return redirect('recrutement:entretiens_programmés')

            except (socket.gaierror, ConnectionError, Exception) as e:
                error_message = f"Une erreur est survenue lors de la création de l'événement: {str(e)}"
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_message}, status=500)
                else:
                    form.add_error(None, error_message) # Ajoute une erreur non liée à un champ
                    # Reprendre le rendu du formulaire avec les erreurs
                    return render(request, 'recrutement/entretiens/ajouter.html', {'form': form, "username": utilisateur})
        else:
            # Si le formulaire n'est pas valide
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            else:
                return render(request, 'recrutement/entretiens/ajouter.html', {'form': form, "username": utilisateur, 'id': id, 'pk': pk})
    else:
        form = EvenementForm()

    return render(request, 'recrutement/entretiens/ajouter.html', {'form': form, "username": utilisateur, 'id': id, 'pk': pk})


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
