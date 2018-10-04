import httplib2
from flask import url_for
from googleapiclient import discovery
from oauth2client import client
from oauth2client.file import Storage

from gcalendar import Calendars

# Fix because http2 lib is not threadsafe (which flask uses when not run in debug mode!)
import httplib2shim
httplib2shim.patch()


SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = r'credentials/client_secret.json'
CREDENTIALS_FILE =  r'credentials/google.creds'
APPLICATION_NAME = 'Ramcal'


class User:

    user = None

    def __init__(self):
        self.credentials = None
        self.service = None
        self.awaiting_credentials = False
        self.user = self

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls.user is not None:
            raise RuntimeError("Attempting to create more than 1 user instance 8O")
        return super().__new__(*args, **kwargs)

    def init_service_from_storage(self):
        storage = Storage(CREDENTIALS_FILE)
        credentials = storage.get()
        if credentials and not credentials.invalid:
            self.credentials = credentials
        else:
            raise KeyError("Couldn't load user credentials")
        self.create_service()

    def init_service_from_code(self, code):
        if not self.awaiting_credentials:
            raise RuntimeError("WTF is going on, no-one asked for this!")
        credentials = self.user.flow.step2_exchange(code)
        self.user.credentials = credentials
        self.awaiting_credentials = False
        self.create_service()

    def save_creds(self):
        storage = Storage(CREDENTIALS_FILE)
        storage.put(self.credentials)

    def create_service(self):
        http = self.credentials.authorize(httplib2.Http())#cache='.cache'))
        service = discovery.build('calendar', 'v3', http=http)
        self.service = service

    def prepare_code_init(self):
        self.flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE,
                                                   scope=SCOPES,
                                                   redirect_uri=url_for('load_credentials', _external=True))
        self.awaiting_credentials = True
        return self.flow.step1_get_authorize_url()

    def get_calendars(self):
        return Calendars(self.service)

    def get_tasks(self):
        return self.get_calendars().primary.future_tasks
