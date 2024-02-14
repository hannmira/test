from os import chdir
from os.path import dirname

chdir(dirname(__file__))

import json
from datetime import datetime, timezone, timedelta

def lck_events_json_to_html():
    with open('lck_events.json', 'r') as f:
        events = json.load(f)

    against = {}
    schedule = {}
    points = {}
    diffs = {}
    teams = ['GEN', 'T1', 'KT', 'HLE', 'DK', 'DRX', 'FOX', 'BRO', 'NS', 'KDF']
    upcomings = {}

    for event in events:
        if datetime.strptime(event['startTime'], "%Y-%m-%dT%H:%M:%SZ") < datetime(2024, 1, 1):
            continue
        if not event['blockName'].startswith('Week'):
            continue

        home = event['match']['teams'][0]['code']
        away = event['match']['teams'][1]['code']

        if event['match']['teams'][0]['result']['outcome']:
            point = 1 if event['match']['teams'][0]['result']['outcome'] == 'win' else -1
            diff = event['match']['teams'][0]['result']['gameWins'] - event['match']['teams'][1]['result']['gameWins']

            points[home] = points.setdefault(home, 0) + point
            points[away] = points.setdefault(away, 0) - point

            diffs[home] = diffs.setdefault(home, 0) + diff
            diffs[away] = diffs.setdefault(away, 0) - diff

            against.setdefault(home, {}).setdefault(away, []).append(point)
            against.setdefault(away, {}).setdefault(home, []).append(-point)

            schedule.setdefault(home, []).append({'vs':away, 'diff':diff})
            schedule.setdefault(away, []).append({'vs':home, 'diff':-diff})

        else:
            schedule.setdefault(home, []).append({'vs':away, 'diff':None})
            schedule.setdefault(away, []).append({'vs':home, 'diff':None})

            if len(upcomings) < 6:
                # 문자열을 datetime 객체로 변환
                datetime_utc = datetime.fromisoformat(event['startTime'].replace('Z', '+00:00'))

                # 한국 시간대는 UTC+9
                datetime_korean = datetime_utc.replace(tzinfo=timezone.utc) + timedelta(hours=9)

                # upcomings.setdefault(datetime_korean.strftime("%b %d %a"),[]).append({"time":datetime_korean.strftime("%H:%M"), "home":home, "away":away})
                upcomings.setdefault(datetime_korean.date(),[]).append({"time":datetime_korean.strftime("%H:%M"), "home":home, "away":away})

    upcomings.popitem()
    teams.sort(key=lambda x: (points[x], diffs[x]), reverse=True)

    str = '''<!DOCTYPE html>
<html>
<head>
<style>
table {margin: 20px;}
th {text-align: center; width: 42px;}
td {text-align: center; width: 36px;}

table, th, td {border-collapse: collapse;}

td.ww {background-color: hsl(200, 100%, 80%);}
td.w {background-color: hsl(200, 100%, 90%);}
td.wl, td.lw {background-color: hsl(50, 100%, 80%);}
td.l {background-color: hsl(20, 100%, 90%);}
td.ll {background-color: hsl(20, 100%, 80%);}
td.na {background-color: #eee;}

table.vs tr {border-bottom: 1px solid #aaa;}
table.vs thead tr, table.vs tr:last-of-type {border-bottom: 1px solid black;}

table.schedule tr {border-bottom: 1px solid black;}
table.schedule thead tr, table.schedule tr:last-of-type {border-bottom: 2px solid black;}
th[scope=row], td.roundlast {border-right: 1px solid #aaa;}

table.upcomings tr {border-top: 1px solid #aaa;}
table.upcomings tr.date {border-top: 1px solid black;}
table.upcomings td.date {width: 102px; text-align: left; vertical-align: top;}
table.upcomings td:nth-last-of-type(4) {width: 52px; text-align:center;}
table.upcomings td:nth-last-of-type(2) {width: 18px;}
table.upcomings td:nth-last-of-type(1), table.upcomings td:nth-last-of-type(3) {width: 56px;font-weight:bold;}
table.upcomings {border-bottom: 1px solid black;}
td.sat {color: hsl(200, 100%, 30%);}
td.sun {color: hsl(20, 100%, 30%);}
</style>
</head>
<body>
<table class="vs">
<thead><tr><td> </td>'''

    for team in teams:
        str += f'<td>{team}</td>'

    str += '<th>Pts</th></tr></thead>\n'

    for team in teams:
        str += f'<tr><th>{team}</th>'
        for vs in teams:
            if team == vs:
                str += '<td class="na">-</td>'
                continue

            text = ''
            style = ''
            for point in against[team].get(vs) or []:
                if point == 1:
                    text = text + '-' + 'W' if text else 'W'
                    style += 'w'
                else:
                    text = text + '-' + 'L' if text else 'L'
                    style += 'l'

            str += f'<td class="{style}">{text}</td>'

        str += f'<td>{points[team]}</td></tr>\n'

    str += '</table>\n\n'
    str += f'<table class="schedule">\n<thead><tr><td> </td><th colspan="{len(teams)-1}">Round 1</th><th colspan="{len(teams)-1}">Round 2</th><th>Pts</th></tr></thead>\n'

    for team in teams:
        str += f'<tr><th scope="row">{team}</th>'
        for i in range(len(schedule[team])):
            match = schedule[team][i]
            if (i+1)%(len(teams)-1) == 0:
                str += '<td class="roundlast '
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
                    str += f'">{match["vs"]}</td>'

        str += f'<td>{points[team]}</td></tr>\n'

    str += "</table>\n"

    str += '<table class="upcomings">\n'
    for date in upcomings.keys():
        match date.weekday():
            case 5:
                str += f'<tr class="date"><td class="date sat"'
            case 6:
                str += f'<tr class="date"><td class="date sun"'
            case _:
                str += f'<tr class="date"><td class="date"'

        str += f' rowspan="{len(upcomings[date])}">{date.strftime("%b %d %a")}</td><td>{upcomings[date][0]["time"]}</td><td>{upcomings[date][0]["home"]}</td><td>vs</td><td>{upcomings[date][0]["away"]}</td></tr>\n'
        for i in range(len(upcomings[date])-1):
            str += f'<tr><td>{upcomings[date][i+1]["time"]}</td><td>{upcomings[date][i+1]["home"]}</td><td>vs</td><td>{upcomings[date][i+1]["away"]}</td></tr>\n'

    str += "</table>\n"
    str += "</body>\n</html>"

    with open("results.html", "w") as html_file:
        html_file.write(str)

if __name__ == "__main__":
    lck_events_json_to_html()