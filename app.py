import json
import datetime
from functools import wraps
import pytz

from flask import Flask, request, url_for, redirect, render_template

from dateutil.parser import parse
from gantt import Gantt
from user import User
from weather import Forecast

import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


# globals
app = Flask(__name__)
user = User()


def logged_in(route):
    @wraps(route)
    def wrapped(*args, **kwargs):
        if not user.service:
            return redirect(user.prepare_login_url())
        return route(*args, **kwargs)
    return wrapped


@app.before_first_request
def try_load_user():
    print("Attempting to load user from storage")
    try:
        user.init_service_from_storage()
        print("success")
    except KeyError:
        pass


@app.route("/")
@logged_in
def home():
    return render_template("vue.html")


@app.route("/api/authenticate_user")
def authenticate_user():
    if not user.credentials:
        user.init_service_from_url(request.url)
        user.store_creds()
    return redirect(url_for('home'))


@logged_in
@app.route("/api/get_calendar")
def get_calendar():
    start = parse(request.args['start'])
    end = parse(request.args['end'])
    cals = user.get_calendars()
    return json.dumps(cals.serialise(start, end))


@app.route("/api/tasks")
@logged_in
def tasks():
    tasks = user.get_tasks()
    if not tasks:
        return "[]"
    now = pytz.utc.localize(datetime.datetime.now())
    gantt = Gantt(now, tasks)
    return json.dumps(gantt.serialise())


@app.route("/api/weather")
def weather():
    day, night, tomorrow = Forecast.current()
    return json.dumps({'day': day.to_json(),
                       'night': night.to_json(),
                       'tomorrow': tomorrow.to_json()})


if __name__ == '__main__':
    app.run(host="127.0.0.1", debug=False, use_reloader=False)