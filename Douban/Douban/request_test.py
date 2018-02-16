import json

import requests

from pprint import pprint
from time import time

from agents import AGENTS

url = 'https://frodo.douban.com/api/v2/movie/tag'

url = 'https://frodo.douban.com/api/v2/movie/tag?alt=json&apikey=0df993c66c0c636e29ecbb5344252a4a&count=20&q=动作%2C西班牙&score_range=0%2C10&sort=T&start=180'
url = 'https://frodo.douban.com/api/v2/movie/tag?alt=json&apikey=0df993c66c0c636e29ecbb5344252a4a&count=20&q=纪录片&score_range=0%2C10&sort=T&start=0'
params = {
    'alt': 'json',
    'apikey': '0df993c66c0c636e29ecbb5344252a4a',
    'count': '20',
    'q': '电影',
    'score_range': '0,10',
    'sort': 'T',
    'start': '0',
}
headers = {'User-Agent': AGENTS[0]}

resp = requests.get(url, headers=headers)
print(resp.url)
print(resp.status_code)
d = json.loads(resp.text)
pprint(d)
print(len(d['data']))
print(d['localized_message'])
