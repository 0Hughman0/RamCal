import json

from flask import url_for

from googleapiclient import discovery
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from gcalendar import Calendars
from google_auth_httplib2 import AuthorizedHttp

# Required to work with Flask - think to do with flask being multithreaded...
import httplib2shim


SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = r'credentials/client_secret.json'
CREDENTIALS_FILE =  r'credentials/google.creds'
APPLICATION_NAME = 'Ramcal'


class User:

    user = None

    def __init__(self):
        self.service = None
        self.flow = None
        self.credentials = None
        self.user = self

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls.user is not None:
            raise RuntimeError("Attempting to create more than 1 user instance 8O")
        return super().__new__(*args, **kwargs)

    def prepare_login_url(self):
        self.flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE,
                                                  scopes=SCOPES,
                                                  redirect_uri=url_for('authenticate_user', _external=True))
        return self.flow.authorization_url(access_type='offline', prompt='consent', include_granted_scopes='true')[0]

    def init_service_from_url(self, url):
        self.flow.fetch_token(authorization_response=url)
        self.credentials = self.flow.credentials

        self._init_service()

    def init_service_from_storage(self):
        try:
            self.credentials = Credentials.from_authorized_user_file(CREDENTIALS_FILE)
        except (FileNotFoundError, json.JSONDecodeError):
            raise KeyError("Couldn't find stored credentials")

        if not self.credentials.valid:
            raise KeyError("Invalid credentials")

        self._init_service()

    def _init_service(self):
        self.service = discovery.build('calendar', 'v3', http=AuthorizedHttp(self.credentials, http=httplib2shim.Http()))

    def store_creds(self):
        with open(CREDENTIALS_FILE, 'w') as f:
            f.write(self.credentials.to_json())

    def get_calendars(self):
        return Calendars(self.service)

    def get_tasks(self):
        return self.get_calendars().primary.future_tasks
