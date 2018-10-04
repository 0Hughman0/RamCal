import json
import datetime
import itertools
import re
from datetime import timedelta, date

from dateutil.parser import parse

from gantt import DEFAULT_ERROR, TaskBar

with open('event_template.json') as f:
    event_template = json.load(f)


class JSONBase:

    map_name = 'google_dict'

    def __getattr__(self, item):
        try:
            return getattr(self, self.map_name)[item]
        except KeyError:
            # Learnt about an interesting/ really hard to debug behaviour, see:
            # https://medium.com/@ceshine/python-debugging-pitfall-mixed-use-of-property-and-getattr-f89e0ede13f1
            # If property raises Attribute error (anywhere!), __getattr__ is called.
            # v- This forces another unavoidable try, which shouldn't suppress any exceptions. -v
            if item in self.__class__.__dict__:
                obj = self.__class__.__dict__[item]
                if hasattr(obj, '__get__'):
                    obj = obj.__get__(self, item)
                return obj
            raise AttributeError(item)


class Event(JSONBase):

    def __init__(self, google_dict, cal):
        self.google_dict = google_dict
        self.cal = cal
        self.task = Task.from_event(google_dict.copy()) # can return None! (for no task)

    @property
    def all_day(self):
        if 'date' in self.google_dict['start'].keys():
            return True
        return False

    @property
    def date_fmt(self):
        fmt = 'dateTime'
        if self.all_day:
            fmt = 'date'
        return fmt

    @property
    def start(self):
        return parse(self.google_dict['start'][self.date_fmt])

    @start.setter
    def start(self, val):
        self.google_dict['start'][self.date_fmt] = val.isoformat()

    @property
    def end(self):
        return parse(self.google_dict['end'][self.date_fmt])

    @end.setter
    def end(self, val):
        self.google_dict['end'][self.date_fmt] = val.isoformat()

    def serialise(self):
        map = self.google_dict.copy()
        map['title'] = self.google_dict.get('summary', '')
        map['start'] = self.start.ctime()
        map['end'] = self.end.ctime()
        map['dallDay'] = self.all_day
        map['color'] = self.cal.colour
        return map


class Task:

    pattern = "#T([0-9]*\.?[0-9]*)"

    def __init__(self, name, target, due, id=None):
        self.name = name
        self.target = timedelta(hours=target)
        self.due = due
        self.id = id

    @classmethod
    def from_event(cls, event):
        """
        returns initialised Task obj
        """
        match = re.search(cls.pattern, event['summary'])
        if not match:
            return None # Bad idea? - nah

        target = float(match.group(1))
        name = match.string[:match.start()].strip()
        if 'dateTime' in event['start']:
            due = parse(event['start']['dateTime'])
        else:
            due = parse(event['start']['date'])
        id = event['id']

        return cls(name, target, due, id)

    @property
    def error(self):
        return self.remaining * DEFAULT_ERROR

    @property
    def remaining(self):
        return self.target

    @property
    def diff(self):
        due = self.due.date()
        today = date.today()
        return due - today

    def to_bar(self, start):
        return TaskBar(start.replace(tzinfo=self.due.tzinfo), self)


class Calendars:

    def __init__(self, service):
        self.service = service
        self.calendars = {map['id']: Calendar(self.service, map) for map in
                          self.service.calendarList().list().execute().get('items', [])}
        cal_cols = self.service.colors().get().execute()['calendar']
        for cal in self.calendars.values():
            cal.colour = cal_cols[cal.colorId]['background']
        self.primary = Calendar(self.service, self.service.calendars().get(calendarId='primary').execute())

    def serialise(self, start, end):
        return list(itertools.chain(*(cal.serialise(start, end) for id, cal in self.calendars.items())))

    def __getitem__(self, item):
        return self.calendars[item]


class Calendar(JSONBase):

    def __init__(self, service, google_dict=None):
        self.service = service
        self.google_dict = google_dict

    def event_list(self, items):
        return [Event(event_dict, self) for event_dict in items]

    def query(self, **kwargs):
        return self.service.events().list(calendarId=self.id, **kwargs).execute().get('items', [])

    @property
    def future_events(self):
        return self.events_from()

    @property
    def future_tasks(self):
        return list(event.task for event in self.future_events if event.task)

    def events_from(self, from_=None, to=None):
        if from_ is None:
            from_ = datetime.datetime.now()

        if from_:
            from_ = from_.isoformat() + 'Z'
        if to:
            to = to.isoformat() + 'Z'

        return self.event_list(self.query(timeMin=from_, timeMax=to))

    def serialise(self, start, end):
        return list(event.serialise() for event in self.events_from(start, end))
