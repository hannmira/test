from os import chdir
from os.path import dirname

chdir(dirname(__file__))

import json
from datetime import datetime, timezone, timedelta

timezone_korean = timezone(timedelta(hours=9))

HTML_HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Short+Stack&display=swap" rel="stylesheet">
<style>
body {font-family: "Short Stack"; font-size: 16px;}
a {color: black; text-decoration: none;}
table {margin: 1em;}
caption {font-weight: bold;}

div.flex-container {display: flex; flex-flow: row wrap;}
div {padding: 0 0.5em;}
div table {margin: 0 0.5em;}

table, th, td {border-collapse: collapse;}
tr {border-bottom: 1px solid black;}
thead tr, tr:last-of-type {border-bottom: 2px solid black;}

th {text-align: center;}
td {text-align: center;}

col.th {width: 42px;}
col.team {width: 38px;}
col.pts {width: 32px;}
table.playoffs col.team {width: 62px;}

td.ww {background-color: hsl(200, 100%, 80%);}
td.w {background-color: hsl(200, 100%, 90%);}
td.wl, td.lw {background-color: hsl(50, 100%, 80%);}
td.l {background-color: hsl(20, 100%, 90%);}
td.ll {background-color: hsl(20, 100%, 80%);}
td.na {background-color: #eee;}
td.pts {font-weight: bold; padding-left: 4px; padding-right: 4px;}
th.pts {padding-left: 2px; padding-right: 2px;}

table.schedule td.pts, td.roundfirst {border-left: 1px solid #aaa;}

table.upcomings {border-top: 2px solid black;}
table.upcomings td.date {text-align: left; vertical-align: top; padding-right: 8px;}
table.upcomings td.time {text-align: center; padding-right: 4px;}
table.upcomings td.vs {text-align: center; padding-left: 4px; padding-right: 4px;}
td.sat {color: hsl(220, 100%, 40%);}
td.sun {color: hsl(0, 100%, 40%);}

tr.datetime {border-bottom: 1px solid #aaa;}
</style>
</head>
<body>
'''

HTML_FOOT = '''</body>
</html>'''

def convert_to_datetime(date_string):
    try:
        datetime_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        datetime_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    return datetime_obj

def lck_events_json_to_html():
    with open('lck_events.json', 'r') as f:
        events = json.load(f)

    h2h = {}
    schedule = {}
    points = {}
    diffs = {}
    teams = ['GEN', 'T1', 'KT', 'HLE', 'DK', 'DRX', 'FOX', 'BRO', 'NS', 'KDF']
    upcomings = {}
    playoffs = {}

    for event in events:
        if convert_to_datetime(event['startTime']) < datetime(2024, 1, 1):
            continue
        if event['type'] != 'match':
            continue
        if not event['blockName'].startswith('Week') and not event['blockName'].startswith('Playoffs'):
            continue

        # 문자열을 datetime 객체로 변환
        datetime_utc = datetime.fromisoformat(event['startTime'].replace('Z', '+00:00'))
        # 한국 시간대는 UTC+9
        datetime_korean = datetime_utc.astimezone(timezone_korean)

        home = event['match']['teams'][0]['code']
        away = event['match']['teams'][1]['code']
        alink = f'<a href="https://oracleselixir.com/matches/{event["match"]["id"]}" target="_blank">'

        today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone_korean)
        if datetime_korean >= today_midnight and datetime_korean < today_midnight + timedelta(days=7):
            upcomings.setdefault(datetime_korean.date(),[]).append({"time":datetime_korean.strftime("%H:%M"), "home":home, "away":away, "alink":alink})

        if event['match']['teams'][0]['result'] and event['match']['teams'][0]['result']['outcome']:
            point = 1 if event['match']['teams'][0]['result']['outcome'] == 'win' else -1
            diff = event['match']['teams'][0]['result']['gameWins'] - event['match']['teams'][1]['result']['gameWins']

            if event['blockName'].startswith('Playoffs'):
                playoffs.setdefault(event['blockName'], []).append({'datetime': datetime_korean, "home":home, "away":away, 'diff':diff, "alink":alink})
                continue

            points[home] = points.setdefault(home, 0) + point
            points[away] = points.setdefault(away, 0) - point

            diffs[home] = diffs.setdefault(home, 0) + diff
            diffs[away] = diffs.setdefault(away, 0) - diff

            schedule.setdefault(home, []).append({'vs':away, 'diff':diff, 'alink':alink})
            schedule.setdefault(away, []).append({'vs':home, 'diff':-diff, 'alink':alink})

            h2h.setdefault(home, {}).setdefault(away, []).append(point)
            h2h.setdefault(away, {}).setdefault(home, []).append(-point)

        else:
            if event['blockName'].startswith('Playoffs'):
                playoffs.setdefault(event['blockName'], []).append({'datetime': datetime_korean, "home":home, "away":away, 'diff':None, "alink":alink})
                continue
            schedule.setdefault(home, []).append({'vs':away, 'diff':None, 'alink':alink})
            schedule.setdefault(away, []).append({'vs':home, 'diff':None, 'alink':alink})

    teams.sort(key=lambda x: (points[x], diffs[x]), reverse=True)

    str = HTML_HEAD

    # upcoming events
    str += '<table class="upcomings">\n'
    str += '<colgroup><col class="date"><col class="time"><col class="th"><col class="vs"><col class="th"></colgroup>\n'
    for date in upcomings.keys():
        for i in range(len(upcomings[date])):
            if i == 0:
                str += '<tr class="date"><td class="date'
                match date.weekday():
                    case 5:
                        str += ' sat"'
                    case 6:
                        str += ' sun"'
                    case _:
                        str += '"'
                str += f' rowspan="{len(upcomings[date])}">{date.strftime("%a, %d %b")}</td>'
            else:
                str += '<tr>'

            alink = upcomings[date][i]["alink"]

            home = upcomings[date][i]["home"]
            homeLt = 100 - (points[home]-points[teams[-1]])/(points[teams[0]]-points[teams[-1]]) * 20
            hometd= f'<th class="team" style="background-color: hsl(50,100%,{homeLt}%)">{alink}{home}</a></td>'

            away = upcomings[date][i]["away"]
            awayLt = 100 - (points[away]-points[teams[-1]])/(points[teams[0]]-points[teams[-1]]) * 20
            awaytd= f'<th class="team" style="background-color: hsl(50,100%,{awayLt}%)">{alink}{away}</a></td>'

            str += f'<td class="time">{alink}{upcomings[date][i]["time"]}</a></td>{hometd}<td class="vs">{alink}vs</a></td>{awaytd}</tr>\n'

    str += "</table>\n\n"

    # playoffs
    str += '<div style="display:flex">\n'
    for round in playoffs.keys():
        str += f'<table class="playoffs">\n<colgroup><col class="team"><col><col class="team"></colgroup>\n<thead><tr><th colspan="3">{round}</th></tr></thead>\n'
        for round_data in playoffs[round]:
            str += '<tr class="datetime"><td colspan="3"'
            match round_data["datetime"].weekday():
                case 5:
                    str += ' class="sat"'
                case 6:
                    str += ' class="sun"'
            str += f'>{round_data["datetime"].strftime("%a, %d %b %H:%M")}</td></tr>\n'
            str += f'<tr class="match"><th>{round_data["home"]}</th><td>vs</td><th>{round_data["away"]}</th></tr>'
        str += "</table>\n"

    str += '</div>\n\n'

    # team schedules
    str += '<table class="schedule">\n'
    str += f'<colgroup><col class="th"><col class="team" span="{len(teams)-1}"><col class="team" span="{len(teams)-1}"><col class="pts"></colgroup>\n'
    str += '<thead><tr><td> </td>'
    for i in range(len(schedule[teams[0]])):
        if i % (len(teams)-1) == 0:
            str += f'<th colspan="{len(teams)-1}">Round {int(i/(len(teams)-1)+1)}</th>'
            i += 1
    str += '<th class="pts">Pts</th></tr></thead>\n'

    for team in teams:
        str += f'<tr><th scope="row">{team}</th>'
        for i in range(len(schedule[team])):
            match = schedule[team][i]
            if i % (len(teams)-1) == 0:
                str += '<td class="roundfirst '
            else:
                str += '<td class=" '
            match match['diff']:
                case 2:
                    str += 'ww">'
                case 1:
                    str += 'w">'
                case -1:
                    str += 'l">'
                case -2:
                    str += 'll">'
                case _:
                    vsLt = 100 - (points[match["vs"]]-points[teams[-1]])/(points[teams[0]]-points[teams[-1]]) * 20
                    str += f'" style="background-color: hsl(50,100%,{vsLt}%)">'
            str += f'{match["alink"]}{match["vs"]}</a></td>'

        str += f'<td class="pts">{points[team]}</td></tr>\n'

    str += "</table>\n\n"

    # h2h
    str += '<table class="vs">\n'
    str += f'<colgroup><col class="th"><col class="team" span="{len(teams)}"><col class="pts"></colgroup>\n'
    str += '<thead><tr><td> </td>'

    for team in teams:
        str += f'<td>{team}</td>'

    str += '<th class="pts">Pts</th></tr></thead>\n'

    for team in teams:
        str += f'<tr><th>{team}</th>'
        for vs in teams:
            if team == vs:
                str += '<td class="na">-</td>'
                continue

            text = ''
            style = ''
            for point in h2h[team].get(vs) or []:
                if point == 1:
                    text = text + '-' + 'W' if text else 'W'
                    style += 'w'
                else:
                    text = text + '-' + 'L' if text else 'L'
                    style += 'l'

            str += f'<td class="{style}">{text}</td>'

        str += f'<td class="pts">{points[team]}</td></tr>\n'

    str += '</table>\n\n'

    str += HTML_FOOT
    with open("results.html", "w") as html_file:
        html_file.write(str)

if __name__ == "__main__":
    lck_events_json_to_html()
