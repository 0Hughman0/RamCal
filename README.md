# RamCal

A dashboard/ calendar webapp written using Python (flask), javascript (vue.js) and using the google calendar and metoffice APIs.

The motivator for this project was to write my own dashboard to have in my room, to help me keep on top of multiple
concurrent tasks.

![Overview](https://raw.githubusercontent.com/0Hughman0/RamCal/master/screenshots/screenshot.png "RamCal")

## Task Gannt

![Gantt](https://raw.githubusercontent.com/0Hughman0/RamCal/master/screenshots/gantt.png "Gantt")

Uniquely RamCal is able to create a Gantt chart of upcoming tasks and display it automatically.

To identify a calendar event as a task, simply put '#Tx' at the end, whereby 'x' is simply the number of hours you
expect the task to take. The due date of the task is taken as the start of the event.

RamCal will then look at your upcoming tasks, and create a Gantt chart, prioritising tasks with the smallest
'end buffer'.

The Gantt is displayed in the top right of the home page. The first bar is simply a scale bar, with blue sections
indicating hours in the day, and black indicating hours at night, up until the due date of the latest deadline.

The bars below are for each task. Blue blocks are 'start buffers', so available time where you don't need to be doing
the task, orange blocks represent the time you have predicted to complete the task, red indicates a 50% error on that
time (configurable in `tasks.py`), and green is the hours left between when you should start, and when you'd be
finished - in other words, the 'buffer'! Tasks are simply ordered such that tasks with a minimal buffer are prioritised.
At present the only way to indicate progress on a task is to edit the number through your existing calendar apps.

## Weather

RamCal is set up to fetch and display weather using the MetOffice API. If you wish to use this feature, you will need
to provide your own API key, which you can get here: https://www.metoffice.gov.uk/datapoint/getting-started.
Unfortunately their forecasts aren't great outside of the UK, so if you're outside the UK, why not create a fork with a
new weather system!? The icons used also come from the metoffice and as such this app "Contains public sector
information licensed under the Open Government Licence v1.0".

`weather.py` can be ran as a standalone file using the command `python weather.py`. This should let you search through
possible locations, by searching for names. Simply enter the name of your usual MetOffice weather location
(case sensitive), and it should find it. Then take the id quoted, set the `LOCATION_ID` parameter at the top of
`weather.py` to that number.

## Setup

1. Clone the repository to wherever you want it with `git clone https://github.com/0Hughman0/RamCal/`
2. Use (pipenv)[https://pipenv.pypa.io/en/latest/] to create a venv and install the dependencies with `pipenv install`.
4. Enter your Met Office API key into `credentials/metffoce.creds` file (see above).
5. Run `weather.py` with `python weather.py`, and follow instructions to find location ID, and replace `LOCAION_ID` (line 8 of `weather.py`) with
your location ID.
6. Set the `FLASK_APP` environment variable to `app.py` with `export FLASK_APP=app.py`. (you can put this into your activate script if you're feeling wizzy).
7. Run the web server with `flask run`
8. In your browser, navigate to `http://127.0.0.1:5000`, your first time, google will ask you to approve access to your
calendar, then it will re-direct you back to the dashboard. These credentials are stored locally (in
`credentials/google.creds`), meaning you won't have to log in every time.


## WARNING

This app is only recommended for use within an internal network, and cannot be exposed to the big bad internet.

## Other Stuff

This app also makes large use of the Full Calendar js library: https://fullcalendar.io/