from os import chdir
from os.path import dirname

chdir(dirname(__file__))

from lolesports_api import Lolesports_API
import json
from os import path, remove, rename
from difflib import unified_diff

def lck_events_to_json():

    if path.exists("lck_events.old"):
        remove("lck_events.old")

    if path.exists("lck_events.json"):
        rename("lck_events.json","lck_events.old")

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

    if path.exists("lck_events.old"):
        with open('lck_events.old') as f1, open('lck_events.json') as f2:
            f1_contents = f1.readlines()
            f2_contents = f2.readlines()

        if f1_contents == f2_contents:
            print("\nNothing changed.")
        else:
            for line in unified_diff(f1_contents, f2_contents, n=0):
                print(line)

if __name__ == "__main__":
    lck_events_to_json()