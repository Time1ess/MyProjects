import re
import sys
import traceback

from pymongo import MongoClient
from elasticsearch import Elasticsearch


db = MongoClient()['Douban']
es = Elasticsearch()

index = 'douban_movies'


# 'directors', 'rate', 'title', 'url', 'casts', 'genres', 'source',
# 'lang', 'release_date', 'runtime', 'aliases', 'imdb_url', 'summary'
mappings = {
    'mappings': {
        'movie': {
            'properties': {
                'directors': {
                    'type': 'text',
                    'fields': {
                        'cn': {
                            'type': 'text',
                            'analyzer': 'ik_max_word',
                            'search_analyzer': 'ik_max_word',
                        },
                        'en': {
                            'type': 'text',
                            'analyzer': 'english',
                        }
                    }
                },
                'rate': {'type': 'double'},
                'title': {
                    'type': 'text',
                    'fields': {
                        'cn': {
                            'type': 'text',
                            'analyzer': 'ik_max_word',
                            'search_analyzer': 'ik_max_word',
                        },
                        'en': {
                            'type': 'text',
                            'analyzer': 'english',
                        }
                    }
                },
                'url': {'type': 'text'},
                'casts': {
                    'type': 'text',
                    'fields': {
                        'cn': {
                            'type': 'text',
                            'analyzer': 'ik_max_word',
                            'search_analyzer': 'ik_max_word',
                        },
                        'en': {
                            'type': 'text',
                            'analyzer': 'english',
                        }
                    }
                },
                'genres': {'type': 'keyword'},
                'source': {'type': 'keyword'},
                'lang': {'type': 'keyword'},
                'release_date': {
                    'type': 'date',
                    'null_value': '0000-00-00',
                },
                'runtime': {'type': 'text'},
                'aliases': {'type': 'keyword'},
                'imdb_url': {'type': 'text'},
                'summary': {
                    'type': 'text',
                    'fields': {
                        'cn': {
                            'type': 'text',
                            'analyzer': 'ik_max_word',
                            'search_analyzer': 'ik_max_word',
                        },
                        'en': {
                            'type': 'text',
                            'analyzer': 'english',
                        }
                    }
                },

            }
        }
    }
}


total = db.command('collstats', 'Movies')['count']
docs = db['Movies'].find(
    {}, projection={
        '_id': False,
        'cover_x': False,
        'cover_y': False,
        'cover': False,
        'star': False,
})


def clean_movie(m):
    parenthesis_pat = re.compile(r'\(.*?\)')
    release_date = '/'.join(m['release_date'])
    release_date = parenthesis_pat.sub('', release_date)
    m['release_date'] = release_date.split('/')
    if not any(m['release_date']):
        del m['release_date']
    if isinstance(m['runtime'], list):
        m['runtime'] = [parenthesis_pat.sub('', x) for x in m['runtime']]
    else:
        m['runtime'] = parenthesis_pat.sub('', m['runtime'])
    return m


if es.indices.exists(index=index):
    es.indices.delete(index=index)
es.indices.create(index=index, body=mappings)

processed = 0
for raw_doc in docs:
    try:
        doc = clean_movie(raw_doc)
        es.index(index=index, doc_type='movie', body=doc)
        processed += 1
        sys.stdout.flush()
        sys.stdout.write(
            'Processed: {:7d} / {:7d}\r'.format(processed, total))
    except Exception as e:
        print(raw_doc)
        print(doc)
        traceback.print_exc()
        break
