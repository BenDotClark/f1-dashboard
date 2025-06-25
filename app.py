from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta

import os
import fastf1
import pandas as pd

# 1) Read cache dir from env, fallback to local 'ff1_cache'
cache_dir = os.environ.get('FASTF1_CACHE_DIR',
                           os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ff1_cache'))
# 2) Ensure it exists
os.makedirs(cache_dir, exist_ok=True)

# 3) Enable FastF1 cache
fastf1.Cache.enable_cache(cache_dir)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, 'static'),
    template_folder=os.path.join(BASE_DIR, 'templates')
)

@app.route('/')
def index():
    """Serve the dashboard HTML."""
    return render_template('index.html')

@app.route('/api/calendar/<int:year>')
def api_calendar(year):
    """Fetch the season calendar via FastF1 and return round, name, date."""
    # FastF1 returns pandas DataFrame for the event schedule
    schedule = fastf1.get_event_schedule(year)

    # Convert DataFrame rows into dicts
    races = []
    for _, ev in schedule.iterrows():
        races.append({
            'round':     int(ev.RoundNumber),
            'raceName':  ev.EventName,
            'date':      ev.EventDate.strftime('%Y-%m-%d')
        })
    return jsonify({'season': year, 'races': races})

@app.route('/api/season/<int:year>/results/<int:rnd>')
def api_season_results(year, rnd):
    """Return race results for a given year & round via FastF1."""
    # read session from query-param, default to 'R'
    session_name = request.args.get('session', 'R').upper()
    # Load race session
    session = fastf1.get_session(year, rnd, session_name)
    session.load(telemetry=False, weather=False, status=False, laps=False) # fetch data / cache

    df = session.results # pandas DataFrame

    results = []
    for row in df.itertuples(index=False):
        # winner’s race time
        t = getattr(row, 'Time', None)
        if isinstance(t, timedelta):
            h, rem = divmod(t.total_seconds(), 3600)
            m, s = divmod(rem, 60)
            time_str = f"{int(h)}:{int(m):02d}:{s:06.3f}"
            gap_str  = ""
        else:
            time_str = ""
            gb = getattr(row, 'TimeBehind', None)
            if isinstance(gb, timedelta):
                gap_str = f"+{gb.total_seconds():.3f}"
            else:
                gap_str = str(gb or "")

        # Now pull the correct team name
        team_name = getattr(row, 'TeamName', '')

        results.append({
            'position': int(getattr(row, 'Position', 0)),
            'driver': getattr(row, 'Abbreviation', getattr(row, 'Driver', '')),
            'constructor': team_name,
            'time':        time_str,
            'gap':         gap_str
        })
    return jsonify({
        'season': year,
        'round': rnd,
        'raceName': session.event['EventName'],
        'session': 'R',
        'results': results
    })

@app.route('/api/latest')
def api_latest():
    """Return the most recent completed race result (defaults to Race session)."""
    year = datetime.now().year
    # get calendar
    schedule = fastf1.get_event_schedule(year)
    today = datetime.now().date()
    valid = []
    for _, ev in schedule.iterrows():
        ev_date = ev.EventDate.date() if hasattr(ev.EventDate, 'date') else None
        if ev_date and ev_date <= today:
            valid.append(ev)
    if not valid:
        return jsonify({'season':year,'round':None,'raceName':None,'session':'R','results':[]})
    latest = max(valid, key=lambda ev: int(ev.RoundNumber))
    return api_season_results(year, int(latest.RoundNumber))

# @app.route('/debug')
# def debug():
#     # pick any season/round/session you know exists
#     sess = fastf1.get_session(2025, 10, 'R')
#     sess.load()
#     df = sess.results

#     # return only the column names
#     return jsonify({
#       'columns': list(df.columns)
#     })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

