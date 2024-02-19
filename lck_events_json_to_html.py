from os import chdir
from os.path import dirname

chdir(dirname(__file__))

import json
from datetime import datetime, timezone, timedelta

timezone_korean = timezone(timedelta(hours=9))

HTML_HEAD = '''<!DOCTYPE html>
<html>
<head>
<style>
.flex-container {display: flex; flex-flow: row wrap;}
caption {font-weight: bold;}
table {margin: 10px;}
table, th, td {border-collapse: collapse;}
tr {border-bottom: 1px solid black;}
thead tr, tr:last-of-type {border-bottom: 2px solid black;}

th {text-align: center;}
td {text-align: center;}

col {width: 38px;}
col.team {width: 42px;}
col.pts {width: 32px;}
col.date {width: 104px;}
col.time {width: 50px;}
col.vs {width: 30px;}

td.ww {background-color: hsl(200, 100%, 80%);}
td.w {background-color: hsl(200, 100%, 90%);}
td.wl, td.lw {background-color: hsl(40, 100%, 80%);}
td.l {background-color: hsl(20, 100%, 90%);}
td.ll {background-color: hsl(20, 100%, 80%);}
td.na {background-color: #eee;}
td.pts {font-weight: bold;}

table.schedule td.pts, td.roundfirst {border-left: 1px solid #aaa;}

table.upcomings {border-top: 2px solid black;}
table.upcomings td.date {text-align: left; vertical-align: top;}
table.upcomings td.time {text-align: left;}
table.upcomings td.team {font-weight: bold;}
td.sat {color: hsl(220, 100%, 40%);}
td.sun {color: hsl(0, 100%, 40%);}
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

    matchvs = {}
    schedule = {}
    points = {}
    diffs = {}
    teams = ['GEN', 'T1', 'KT', 'HLE', 'DK', 'DRX', 'FOX', 'BRO', 'NS', 'KDF']
    upcomings = {}

    for event in events:
        if convert_to_datetime(event['startTime']) < datetime(2024, 1, 1):
            continue
        if event['type'] != 'match':
            continue
        if not event['blockName'].startswith('Week'):
            continue

        # 문자열을 datetime 객체로 변환
        datetime_utc = datetime.fromisoformat(event['startTime'].replace('Z', '+00:00'))
        # 한국 시간대는 UTC+9
        datetime_korean = datetime_utc.astimezone(timezone_korean)

        home = event['match']['teams'][0]['code']
        away = event['match']['teams'][1]['code']

        today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone_korean)
        if datetime_korean >= today_midnight and datetime_korean < today_midnight + timedelta(days=7):
            upcomings.setdefault(datetime_korean.date(),[]).append({"time":datetime_korean.strftime("%H:%M"), "home":home, "away":away})

        if event['match']['teams'][0]['result']['outcome']:
            point = 1 if event['match']['teams'][0]['result']['outcome'] == 'win' else -1
            diff = event['match']['teams'][0]['result']['gameWins'] - event['match']['teams'][1]['result']['gameWins']

            points[home] = points.setdefault(home, 0) + point
            points[away] = points.setdefault(away, 0) - point

            diffs[home] = diffs.setdefault(home, 0) + diff
            diffs[away] = diffs.setdefault(away, 0) - diff

            matchvs.setdefault(home, {}).setdefault(away, []).append(point)
            matchvs.setdefault(away, {}).setdefault(home, []).append(-point)

            schedule.setdefault(home, []).append({'vs':away, 'diff':diff})
            schedule.setdefault(away, []).append({'vs':home, 'diff':-diff})

        else:
            schedule.setdefault(home, []).append({'vs':away, 'diff':None})
            schedule.setdefault(away, []).append({'vs':home, 'diff':None})

    teams.sort(key=lambda x: (points[x], diffs[x]), reverse=True)

    str = HTML_HEAD

    # upcoming events
    str += '<table class="upcomings">\n'
    str += '<colgroup><col class="date"><col class="time"><col class="team"><col class="vs"><col class="team"></colgroup>\n'
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
                str += f' rowspan="{len(upcomings[date])}">{date.strftime("%b %d %a")}</td>'
            else:
                str += '<tr>'

            home = upcomings[date][i]["home"]
            homeLt = 100 - (points[home]-points[teams[-1]])/(points[teams[0]]-points[teams[-1]]) * 20
            hometd= f'<td class="team" style="background-color: hsl(40,100%,{homeLt}%)">{home}</td>'

            away = upcomings[date][i]["away"]
            awayLt = 100 - (points[away]-points[teams[-1]])/(points[teams[0]]-points[teams[-1]]) * 20
            awaytd= f'<td class="team" style="background-color: hsl(40,100%,{awayLt}%)">{away}</td>'

            str += f'<td class="time">{upcomings[date][i]["time"]}</td>{hometd}<td>vs</td>{awaytd}</tr>\n'

    str += "</table>\n\n"

    # team schedules
    str += '<table class="schedule">\n'
    str += f'<colgroup><col class="team"><col span="{len(teams)-1}"><col span="{len(teams)-1}"><col class="pts"></colgroup>\n'
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
                    str += f'ww">{match["vs"]}</td>'
                case 1:
                    str += f'w">{match["vs"]}</td>'
                case -1:
                    str += f'l">{match["vs"]}</td>'
                case -2:
                    str += f'll">{match["vs"]}</td>'
                case _:
                    vsLt = 100 - (points[match["vs"]]-points[teams[-1]])/(points[teams[0]]-points[teams[-1]]) * 20
                    str += f'" style="background-color: hsl(40,100%,{vsLt}%)">{match["vs"]}</td>'

        str += f'<td class="pts">{points[team]}</td></tr>\n'

    str += "</table>\n\n"

    # team vs
    str += '<table class="vs">\n'
    str += f'<colgroup><col class="team"><col span="{len(teams)}"><col class="pts"></colgroup>\n'
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
            for point in matchvs[team].get(vs) or []:
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
