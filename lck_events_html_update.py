from os import chdir
from os.path import dirname

chdir(dirname(__file__))

from lck_events_to_json import lck_events_to_json
from lck_events_json_to_html import lck_events_json_to_html

lck_events_to_json()
lck_events_json_to_html()