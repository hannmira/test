from os import chdir
from os.path import dirname

chdir(dirname(__file__))

import json
from datetime import datetime

def lck_events_json_to_html():
    with open('lck_events.json', 'r') as f:
        events = json.load(f)

    against = {}
    schedule = {}
    points = {}
    diffs = {}
    teams = ['GEN', 'T1', 'KT', 'HLE', 'DK', 'DRX', 'FOX', 'BRO', 'NS', 'KDF']

    for event in events:
        if datetime.strptime(event['startTime'], "%Y-%m-%dT%H:%M:%SZ") < datetime(2024, 1, 1):
            continue
        if not event['blockName'].startswith('Week'):
            continue

        home = event['match']['teams'][0]['code']
        away = event['match']['teams'][1]['code']

        if event['state'] == 'completed':
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

    teams.sort(key=lambda x: (points[x], diffs[x]), reverse=True)

    for team in teams:
        print(f'{team}\t{points[team]}\t{diffs[team]}')

    str = '''<!DOCTYPE html>
<html>
<head>
<style>
table {margin: 20px;}
th {text-align: center; width: 42px;}
td {text-align: center; width: 36px;}
tr {border-bottom: 1px solid #888;}
table, th, td {border-collapse: collapse;}
td.ww {background-color: hsl(200, 100%, 80%);}
td.w {background-color: hsl(200, 100%, 90%);}
td.wl, td.lw {background-color: hsl(50, 100%, 80%);}
td.l {background-color: hsl(20, 100%, 90%);}
td.ll {background-color: hsl(20, 100%, 80%);}
td.na {background-color: #eee;}

table.schedule, table.schedule thead {border-bottom: 2px solid black;}
table.schedule tr {border-bottom: 1px solid black;}
thead tr {border-bottom: 2px solid black;}
th[scope=row], td.lastround {border-right: 1px solid #aaa;}
</style>
</head>
<body>
<table>
<tr><td> </td>'''

    for team in teams:
        str += f'<td>{team}</td>'

    str += '<th>Pts</th>'

    for team in teams:
        str += f'</tr>\n<tr><th>{team}</th>'
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

        str += f'<td>{points[team]}</td>'

    str += '</tr>\n</table>\n\n'
    str += f'<table class="schedule">\n<thead><tr><td> </td><th colspan="{len(teams)-1}">Round 1</th><th colspan="{len(teams)-1}">Round 2</th><th>Pts</th></tr></thead>\n'

    for team in teams:
        str += f'<tr><th scope="row">{team}</th>'
        for i in range(len(schedule[team])):
            match = schedule[team][i]
            if (i+1)%(len(teams)-1) == 0:
                str += '<td class="lastround '
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

    str += "</table>\n</body>\n</html>"

    with open("results.html", "w") as html_file:
        html_file.write(str)

if __name__ == "__main__":
    lck_events_json_to_html()