import json

import requests

from pprint import pprint

from agents import AGENTS


url = 'https://www.zhihu.com/api/v4/members/xu-wang-liu-nian/followees?offset=0&limit=20'
headers = {
    'User-Agent': AGENTS[1],
    'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'}

resp = requests.get(url, headers=headers)
print(resp.url)
print(resp.status_code)
d = json.loads(resp.text)
pprint(d)
