from os import chdir
from os.path import dirname

chdir(dirname(__file__))

from lolesports_api import Lolesports_API
import json

def lck_events_to_json():

    api = Lolesports_API()
    data = api.get_schedule(league_id=98767991310872058)

    olderPageToken = data['schedule']['pages']['older']
    pageToken = data['schedule']['pages']['newer']
    events = data['schedule']['events']

    data = api.get_schedule(league_id=98767991310872058, pageToken=olderPageToken)
    events = data['schedule']['events'] + events

    while pageToken:
        data = api.get_schedule(league_id=98767991310872058, pageToken=pageToken)
        pageToken = data['schedule']['pages']['newer']
        events += data['schedule']['events']

    with open("lck_events.json", "w") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    lck_events_to_json()