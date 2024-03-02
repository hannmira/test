from os import chdir
from os.path import dirname

chdir(dirname(__file__))

import json
from datetime import datetime, timezone, timedelta

timezone_korean = timezone(timedelta(hours=9))

HTML_HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=874" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Short+Stack&display=swap" rel="stylesheet">
<style>
body {font-family: "Short Stack"; font-size: 16px;}
a {color: black; text-decoration: none;}

table {margin: 1em 0.5em;}
div {margin: 1em 0;}
div.flex-container {display: flex; flex-flow: row wrap; align-items: flex-start;}
div table {margin: 0 0.5em;}
div table+table.week {margin: 0 1.5em;}

table, th, td {border-collapse: collapse;}
tr {border-bottom: 1px solid black;}
thead tr, tr:last-of-type {border-bottom: 2px solid black;}

th {text-align: center; padding: 0 4px; white-space: nowrap;}
td {text-align: center; padding: 0 2px;}
td.na {background-color: #eee;}
td.w_l, td.pts {font-weight: bold;}

col.team {width: 40px;}
table.playoffs col.team {width: 62px;}

table.schedule td.w_l, td.roundfirst {border-left: 1px solid black;}

table.week {border-top: 2px solid black;}
td.date {text-align: left; vertical-align: top; padding-right: 1em;}
table.week td.time {padding-right: 4px;}
table.week td.vs {padding: 0 4px;}
td.sat {color: hsl(220, 100%, 40%);}
td.sun {color: hsl(0, 100%, 40%);}

tr.datetime {border-bottom: 1px solid #ccc;}
</style>
</head>
<body>
'''

HTML_FOOT = '''</body>
</html>'''

w_l = {}
pts = {}
teams = ['GEN', 'T1', 'KT', 'HLE', 'DK', 'DRX', 'FOX', 'BRO', 'NS', 'KDF']

def convert_to_datetime(date_string):
    try:
        datetime_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        datetime_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    return datetime_obj

def team_style(team, set):
    if set > 0:
        return f'"background-color: hsl(200, 100%, {100-set*10}%)"'
    elif set < 0:
        return f'"background-color: hsl(20, 100%, {100+set*10}%)"'
    elif team in w_l:
        Lt = 100 - (w_l[team]-w_l[teams[-1]])/(w_l[teams[0]]-w_l[teams[-1]]) * 20
        return f'"background-color: hsl(50,100%,{Lt}%)"'
    elif team:
        return '""'
    else:
        return '"background-color: hsl(50, 100%, 80%)"'

def lck_events_json_to_html():
    with open('lck_events.json', 'r') as f:
        events = json.load(f)

    h2h = {}
    schedule = {}
    thisweek = {}
    nextweek = {}
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

        set = 0
        win = 0
        home = event['match']['teams'][0]['code']
        away = event['match']['teams'][1]['code']
        alink = f'<a href="https://oracleselixir.com/matches/{event["match"]["id"]}" target="_blank">'

        if event['match']['teams'][0]['result'] and event['match']['teams'][0]['result']['outcome']:
            win = 1 if event['match']['teams'][0]['result']['outcome'] == 'win' else -1
            set = event['match']['teams'][0]['result']['gameWins'] - event['match']['teams'][1]['result']['gameWins']

        today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone_korean)
        today_weekday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone_korean).weekday()
        if datetime_korean >= today_midnight - timedelta(days=today_weekday) and datetime_korean < today_midnight + timedelta(days=(7-today_weekday)):
            thisweek.setdefault(datetime_korean.date(),[]).append({"time":datetime_korean.strftime("%H:%M"), "home":home, "away":away, "set":set, "alink":alink})
        elif datetime_korean >= today_midnight + timedelta(days=(7-today_weekday)) and datetime_korean < today_midnight + timedelta(days=(14-today_weekday)):
            nextweek.setdefault(datetime_korean.date(),[]).append({"time":datetime_korean.strftime("%H:%M"), "home":home, "away":away, "set":set, "alink":alink})

        if event['blockName'].startswith('Playoffs'):
            playoffs.setdefault(event['blockName'], []).append({'datetime': datetime_korean, "home":home, "away":away, 'set':set, "alink":alink})
            continue

        schedule.setdefault(home, []).append({'vs':away, 'set':set, 'alink':alink})
        schedule.setdefault(away, []).append({'vs':home, 'set':-set, 'alink':alink})

        if win and set:
            w_l[home] = w_l.setdefault(home, 0) + win
            w_l[away] = w_l.setdefault(away, 0) - win

            pts[home] = pts.setdefault(home, 0) + set
            pts[away] = pts.setdefault(away, 0) - set

            h2h.setdefault(home, {}).setdefault(away, []).append(win)
            h2h.setdefault(away, {}).setdefault(home, []).append(-win)

    teams.sort(key=lambda x: (w_l[x], pts[x]), reverse=True)

    str = HTML_HEAD

    str += '<div style="display:flex">\n'
    # events in this week
    str += '<table class="week">\n'
    str += '<colgroup><col class="date"><col class="time"><col class="th"><col class="vs"><col class="th"></colgroup>\n'
    for date in thisweek.keys():
        for i in range(len(thisweek[date])):
            if i == 0:
                match date.weekday():
                    case 5:
                        weekday = ' sat'
                    case 6:
                        weekday = ' sun'
                    case _:
                        weekday = ''
                str += f'<tr><td class="date {weekday}" rowspan="{len(thisweek[date])}">{date.strftime("%a")}, {date.strftime("%d %b")}</td>'
            else:
                str += '<tr>'

            alink = thisweek[date][i]["alink"]

            home = thisweek[date][i]["home"]
            hometd= f'<th class="team" style={team_style(home, thisweek[date][i]["set"])}>{alink}{home}</a></td>'

            away = thisweek[date][i]["away"]
            awaytd= f'<th class="team" style={team_style(away, -thisweek[date][i]["set"])}>{alink}{away}</a></td>'

            str += f'<td class="time">{alink}{thisweek[date][i]["time"]}</a></td>{hometd}<td class="vs">{alink}vs</a></td>{awaytd}</tr>\n'

    str += "</table>\n\n"

    # events in next week
    str += '<table class="week">\n'
    str += '<colgroup><col class="date"><col class="time"><col class="th"><col class="vs"><col class="th"></colgroup>\n'
    for date in nextweek.keys():
        for i in range(len(nextweek[date])):
            if i == 0:
                match date.weekday():
                    case 5:
                        weekday = ' sat'
                    case 6:
                        weekday = ' sun'
                    case _:
                        weekday = ''
                str += f'<tr><td class="date {weekday}" rowspan="{len(nextweek[date])}">{date.strftime("%a")}, {date.strftime("%d %b")}</td>'
            else:
                str += '<tr>'

            alink = nextweek[date][i]["alink"]

            home = nextweek[date][i]["home"]
            hometd= f'<th class="team" style={team_style(home, nextweek[date][i]["set"])}>{alink}{home}</a></td>'

            away = nextweek[date][i]["away"]
            awaytd= f'<th class="team" style={team_style(away, -nextweek[date][i]["set"])}>{alink}{away}</a></td>'

            str += f'<td class="time">{alink}{nextweek[date][i]["time"]}</a></td>{hometd}<td class="vs">{alink}vs</a></td>{awaytd}</tr>\n'

    str += "</table>\n\n"
    str += '</div>\n\n'

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
            str += f'<tr class="match"><th style={team_style(round_data["home"], round_data["set"])}>{round_data["home"]}</th><td>vs</td><th style={team_style(round_data["away"], -round_data["set"])}>{round_data["away"]}</th></tr>'
        str += "</table>\n"

    str += '</div>\n\n'

    # team schedules
    str += '<table class="schedule">\n'
    str += f'<colgroup><col class="th"><col class="team" span="{len(teams)-1}"><col class="team" span="{len(teams)-1}"><col class="w_l"></colgroup>\n'
    str += '<thead><tr><td> </td>'
    for i in range(len(schedule[teams[0]])):
        if i % (len(teams)-1) == 0:
            str += f'<th colspan="{len(teams)-1}">Round {int(i/(len(teams)-1)+1)}</th>'
            i += 1
    str += '<th class="w_l">W-L</th><th>Pts</th></tr></thead>\n'

    for team in teams:
        str += f'<tr><th scope="row">{team}</th>'
        for i in range(len(schedule[team])):
            match = schedule[team][i]
            if i % (len(teams)-1) == 0:
                str += '<td class="roundfirst"'
            else:
                str += '<td'

            str += f' style={team_style(match["vs"], match["set"])}>{match["alink"]}{match["vs"]}</a></td>'

        str += f'<td class="w_l">{w_l[team]}</td><td class="pts">{pts[team]}</td></tr>\n'

    str += "</table>\n\n"

    # h2h
    str += '<table class="vs">\n'
    str += f'<colgroup><col class="th"><col class="team" span="{len(teams)}"><col class="w_l"></colgroup>\n'
    str += '<thead><tr><td> </td>'

    for team in teams:
        str += f'<td>{team}</td>'

    str += '<th class="w_l">W-L</th><th>Pts</th></tr></thead>\n'

    for team in teams:
        str += f'<tr><th>{team}</th>'
        for vs in teams:
            if team == vs:
                str += '<td class="na">-</td>'
                continue

            text = ''
            set = 0
            for win in h2h[team].get(vs) or []:
                if win == 1:
                    text += 'W'
                else:
                    text += 'L'
                set += win

            if text:
                str += f'<td style={team_style(None, set)}>{text}</td>'
            else:
                str += f'<td></td>'

        str += f'<td class="w_l">{w_l[team]}</td><td class="pts">{pts[team]}</td></tr>\n'

    str += '</table>\n\n'

    str += HTML_FOOT
    with open("results.html", "w") as html_file:
        html_file.write(str)

if __name__ == "__main__":
    lck_events_json_to_html()
