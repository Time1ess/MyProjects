from pprint import pprint
from collections import namedtuple
from urllib.parse import quote, unquote

import requests

from elasticsearch import Elasticsearch


es = Elasticsearch()
index = 'douban_movies'

query_item = namedtuple('QueryItem',
                        ['absolute', 'positive', 'restrictive',
                         'field', 'value'])
reserved_keywords = ['!', '-', '?']
field_mappings = {
    '主演': 'casts.cn',
    '片名': 'title.cn',
    '类型': 'genres',
    '导演': 'directors',
    '评分': 'rate',
    '来源': 'source',
    '语言': 'lang',
    '日期': 'release_date',
    '片长': 'runtime',
    '别名': 'aliases',
    '简介': 'summary',
}


def parse_value(value):
    return value.replace(',', ' ')


def parse_query_item(q):
    positive = True
    absolute = False
    restrictive = True
    while q[0] in reserved_keywords:
        if q.startswith('-'):
            q = q[1:]
            positive = False
        elif q.startswith('!'):
            q = q[1:]
            absolute = True
        elif q.startswith('?'):
            q = q[1:]
            restrictive = False
    *field, value = q.split(':', 1)
    if not field:
        field = 'title'
    else:
        field = field_mappings[field[0]]
    value = parse_value(value)
    item = query_item(absolute, positive, restrictive, field, value)
    return item


def parse_query(escaped_query, offset, limit):
    unescaped_query = unquote(escaped_query)
    # query_list = unquote(escaped_query).split(' ')
    must = []
    must_not = []
    should = []
    for q in unescaped_query.split(' '):
        item = parse_query_item(q)
        if item.positive is False:
            target = must_not
        else:
            if item.restrictive is True:
                target = must
            else:
                target = should
        search_type = 'match' if not item.absolute else 'term'
        target.append({search_type: {item.field: item.value}})
    query = {
        'must': must,
        'must_not': must_not,
        'should': should
    }
    pprint(query)
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


if __name__ == '__main__':
    query = quote('钢铁侠 -片名:钢管侠 !主演:罗伯特 ?语言:英语')
    print(search(query)['hits']['hits'][0])
