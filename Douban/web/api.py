from pprint import pprint
from urllib.parse import quote, unquote

import requests

from elasticsearch import Elasticsearch


es = Elasticsearch()
index = 'douban_movies'


def advanced_parse(query_list):
    """
    Parse query like 'title:Iron man'
    """
    pass


def parse_query(escaped_query, offset, limit):
    unescaped_query = unquote(escaped_query)
    # query_list = unquote(escaped_query).split(' ')
    query = {'must': {'match': {'title': unescaped_query}}}
    return build_query(offset, limit, **query)


def build_query(offset, limit, **query):
    q = {
        'from': offset,
        'size': limit,
        'query': {
            'bool': {}
        }
    }
    q['query']['bool'].update(query)
    return q


def search(query, offset=0, limit=10):
    query = parse_query(query, offset, limit)
    url = 'http://localhost:9200/douban_movies/movie/_search'
    data = requests.post(url, json=query).json()
    return data


# query = quote('钢铁侠 -钢铁人 lang:英语,德语 genres:科幻')
if __name__ == '__main__':
    query = quote('钢铁侠')
    print(search(query)['hits']['hits'][0])
