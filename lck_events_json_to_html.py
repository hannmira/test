from os import chdir
from os.path import dirname

chdir(dirname(__file__))

import json
from datetime import datetime, timezone, timedelta

HTML_HEAD = '''<!DOCTYPE html>
<html>
<head>
<style>
.flex-container {display: flex; flex-flow: row wrap;}
caption {font-weight:bold;}
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
td.wl, td.lw {background-color: hsl(50, 100%, 80%);}
td.l {background-color: hsl(20, 100%, 90%);}
td.ll {background-color: hsl(20, 100%, 80%);}
td.na {background-color: #eee;}

table.schedule th[scope=row], td.roundlast {border-right: 1px solid #aaa;}

table.upcomings {border-top: 2px solid black;}
table.upcomings td.date {text-align: left; vertical-align: top;}
table.upcomings td.time {text-align: left;}
table.upcomings td.team {font-weight:bold;}
td.sat {color: hsl(200, 100%, 30%);}
td.sun {color: hsl(20, 100%, 30%);}
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
    roundmatchvs = []
    oneroundmatchvs = {}

    index = 0
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
        datetime_korean = datetime_utc.replace(tzinfo=timezone.utc) + timedelta(hours=9)

        home = event['match']['teams'][0]['code']
        away = event['match']['teams'][1]['code']
        diff = 0

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

            if len(upcomings) < 6:
                upcomings.setdefault(datetime_korean.date(),[]).append({"time":datetime_korean.strftime("%H:%M"), "home":home, "away":away})

        oneroundmatchvs.setdefault(home, {})[away] = {'date':datetime_korean.strftime("%#m/%#d"), 'diff':diff}
        oneroundmatchvs.setdefault(away, {})[home] = {'date':datetime_korean.strftime("%#m/%#d"), 'diff':-diff}

        if index % (len(teams)*(len(teams)-1)/2) == (len(teams)*(len(teams)-1)/2)-1:
            roundmatchvs.append(oneroundmatchvs)
            oneroundmatchvs = {}

        index += 1

    upcomings.popitem()
    teams.sort(key=lambda x: (points[x], diffs[x]), reverse=True)

    str = HTML_HEAD
    str += '<table class="vs">\n'
    str += f'<colgroup><col class="team"><col span="{len(teams)}"><col class="pts"></colgroup>\n'
    str += '<thead><tr><td> </td>'

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
            for point in matchvs[team].get(vs) or []:
                if point == 1:
                    text = text + '-' + 'W' if text else 'W'
                    style += 'w'
                else:
                    text = text + '-' + 'L' if text else 'L'
                    style += 'l'

            str += f'<td class="{style}">{text}</td>'

        str += f'<td>{points[team]}</td></tr>\n'

    str += '</table>\n\n'

    str += '<div class="flex-container">\n'
    for index in range(len(roundmatchvs)):
        oneround = roundmatchvs[index]

        str += '<table class="vs">\n'
        str += f'<caption>Round {index+1}</caption>\n'
        str += f'<colgroup><col class="team"><col span="{len(teams)}"><col class="pts"></colgroup>\n'
        str += '<thead><tr><td> </td>'

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
                match oneround[team][vs].get("diff"):
                    case 2:
                        style = 'ww'
                    case 1:
                        style = 'w'
                    case -1:
                        style = 'l'
                    case -2:
                        style = 'll'
                str += f'<td class="{style}">{oneround[team][vs]["date"]}</td>'

            str += f'<td>{points[team]}</td></tr>\n'

        str += '</table>\n'

    str += '</div>\n\n'

    str += '<table class="schedule">\n'
    str += f'<colgroup><col class="team"><col span="{len(teams)-1}"><col span="{len(teams)-1}"><col class="pts"></colgroup>\n'
    str += f'<thead><tr><td> </td><th colspan="{len(teams)-1}">Round 1</th><th colspan="{len(teams)-1}">Round 2</th><th>Pts</th></tr></thead>\n'

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

    str += "</table>\n\n"

    str += '<div class="flex-container">\n<table class="upcomings">\n'
    str += '<colgroup><col class="date"><col class="time"><col class="team"><col class="vs"><col class="team"></colgroup>\n'
    for date in upcomings.keys():
        str += '<tr class="date"><td class="date'

        match date.weekday():
            case 5:
                str += ' sat"'
            case 6:
                str += ' sun"'
            case _:
                str += '"'

        str += f' rowspan="{len(upcomings[date])}">{date.strftime("%b %d %a")}</td>'

        home = upcomings[date][0]["home"]
        homeHue = (points[home]-points[teams[-1]])/(points[teams[0]]-points[teams[-1]]) * 80 + 20
        hometd= f'<td class="team" style="background-color: hsl({homeHue},100%,90%)">{home}</td>'

        away = upcomings[date][0]["away"]
        awayHue = (points[away]-points[teams[-1]])/(points[teams[0]]-points[teams[-1]]) * 80 + 20
        awaytd= f'<td class="team" style="background-color: hsl({awayHue},100%,90%)">{away}</td>'

        str += f'<td class="time">{upcomings[date][0]["time"]}</td>{hometd}<td>vs</td>{awaytd}</tr>\n'

        for i in range(len(upcomings[date])-1):
            home = upcomings[date][i+1]["home"]
            homeHue = (points[home]-points[teams[-1]])/(points[teams[0]]-points[teams[-1]]) * 80 + 20
            hometd= f'<td class="team" style="background-color: hsl({homeHue},100%,90%)">{home}</td>'

            away = upcomings[date][i+1]["away"]
            awayHue = (points[away]-points[teams[-1]])/(points[teams[0]]-points[teams[-1]]) * 80 + 20
            awaytd= f'<td class="team" style="background-color: hsl({awayHue},100%,90%)">{away}</td>'

            str += f'<tr><td class="time">{upcomings[date][i+1]["time"]}</td>{hometd}<td>vs</td>{awaytd}</tr>\n'

    str += "</table>\n</div>\n\n"
    str += HTML_FOOT

    with open("results.html", "w") as html_file:
        html_file.write(str)

if __name__ == "__main__":
    lck_events_json_to_html()

