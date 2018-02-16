import json

import requests

from pprint import pprint

from agents import AGENTS

url = 'https://frodo.douban.com/api/v2/movie/1295644'
# url = 'https://frodo.douban.com/api/v2/movie/4861417?alt=json&apikey=0df993c66c0c636e29ecbb5344252a4a'
# url = 'https://frodo.douban.com/api/v2/movie/1395357?alt=json&apikey=0df993c66c0c636e29ecbb5344252a4a'
params = {
    'alt': 'json',
    'apikey': '0df993c66c0c636e29ecbb5344252a4a',
}
headers = {'User-Agent': AGENTS[0]}

resp = requests.get(url, headers=headers, params=params)
# resp = requests.get(url, headers=headers)
print(resp.url)
print(resp.status_code)
d = json.loads(resp.text)
pprint(d)
if resp.status_code == 200:
    pass
else:
    print(d['localized_message'])
