import math

import api

from urllib.parse import quote
from flask import Flask, render_template, request


app = Flask(__name__)
LIMIT = 10


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args['query']
    page = int(request.args.get('page', 1))
    context = api.search(query, limit=LIMIT, offset=(page-1)*LIMIT)
    total = context['hits']['total']
    pages = int(math.ceil(total / 10))
    context['first_page'] = 1
    context['min_page'] = max(1, page - 2)
    context['max_page'] = min(pages, context['min_page'] + 4)
    context['last_page'] = pages
    context['current_page'] = page
    context['query'] = query
    return render_template('results.html', **context)


if __name__ == '__main__':
    app.run()
