# -*- coding: utf-8 -*-
import json
import re
import itertools
import urllib.parse as up

import pymongo
import scrapy

from scrapy.http import Request

from Douban.settings import MONGO_HOST, MONGO_PORT, MONGO_DB
from Douban.const import movie_genres, movie_nations, genres
from Douban.items import MovieItem


class MovieSpider(scrapy.Spider):
    name = 'Movie'
    allowed_domains = ['movie.douban.com']
    api_url = ('https://movie.douban.com/j/new_search_subjects?'
               'sort=T&range=0,10&tags={tags}&start={offset}')
    offset = 20
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    db = client[MONGO_DB]
    collection = db['Movies']

    def is_duplicated_item(self, _id):
        if self.collection.find_one({'_id': _id}) is not None:
            return True
        return False

    def start_requests(self):
        for tag in itertools.chain(movie_genres, movie_nations):
            meta = {'tags': tag, 'offset': 0}
            url = self.api_url.format(**meta)
            yield Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        if response.status == 400:
            try:
                msg = json.loads(response.text)['msg']
                if msg.startswith('rate_limit'):
                    raise CloseSpider("Rate_Limit_Exceeded")
            except Exception:
                return response.request
        if response.status != 200:
            return response.request
        meta = response.request.meta
        meta['offset'] += self.offset
        url = self.api_url.format(**meta)
        data_dict = json.loads(response.text)['data']
        if len(data_dict) != 0:
            yield Request(url, callback=self.parse, meta=meta)
        for d in data_dict:
            url = d['url']
            _id = d['id']
            if self.is_duplicated_item(_id):
                continue
            yield Request(
                url, callback=self.parse_item, meta={'data': d},
                priority=1)

    def parse_item(self, response):
        if response.status == 400:
            try:
                msg = json.loads(response.text)['msg']
                if msg.startswith('rate_limit'):
                    raise CloseSpider("Rate_Limit_Exceeded")
            except Exception:
                return response.request
        if response.status != 200:
            return response.request
        data = response.request.meta['data']
        pat = re.compile('<.*?>')
        info = response.xpath('//div[@id="info"]').extract_first()
        info = re.sub(pat, '', info).split('\n')
        info = [x.replace(' ', '') for x in info]
        info = [x for x in info if x != '']
        info = [x.split(':', 1) for x in info]
        info = [x for x in info if len(x) == 2]
        info = dict(info)
        info = {
            'genres': info.get('类型', 'Unknown').split('/'),
            'source': info.get('制片国家/地区', 'Unknown').split('/'),
            'lang': info.get('语言', 'Unknown').split('/'),
            'release_date': info.get('上映日期', '-1').split('/'),
            'runtime': info.get('片长', 'Unknown'),
            'aliases': info.get('又名', '').split('/'),
            'imdb_url': info.get('IMDb链接', ''),
        }
        summary = response.xpath(
            '//div[@id="link-report"]//span[@property="v:summary"]/text()')
        summary = summary.extract_first().strip()
        info['summary'] = summary
        data.update(info)
        data['rate'] = float(data['rate'])
        data['_id'] = data['id']
        del data['id']
        item = MovieItem(data)
        yield item


class MMovieSpider(scrapy.Spider):
    name = 'MMovie'
    allowed_domains = ['frodo.douban.com']
    api_url = 'https://frodo.douban.com/api/v2/movie/tag'
    detail_api_url = 'https://frodo.douban.com/api/v2/movie'
    params = {
        'alt': 'json',
        'apikey': '0df993c66c0c636e29ecbb5344252a4a',
        'count': '20',
        'q': '电影',
        'score_range': '0,10',
        'sort': 'T',
        'start': 0,
    }
    detail_params = {
        'alt': 'json',
        'apikey': '0df993c66c0c636e29ecbb5344252a4a',
    }
    offset = 20
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    db = client[MONGO_DB]
    collection = db['Movies']

    def is_duplicated_item(self, _id):
        if self.collection.find_one({'_id': _id}) is not None:
            return True
        return False

    @staticmethod
    def generate_tag_combination(genres, genres_cnt, nations, nations_cnt):
        return [genres] * genres_cnt + [nations] * nations_cnt

    def start_requests(self):
        cnts = [(0, 1), (1, 0), (1, 1)]
        for genres_cnt, nations_cnt in cnts:
            tags_combinations = self.generate_tag_combination(
                movie_genres, genres_cnt, movie_nations, nations_cnt)
            for tags in itertools.product(*tags_combinations):
                params = self.params.copy()
                params['q'] = ','.join(tags)
                url = '{}?{}'.format(self.api_url, up.urlencode(params))
                yield Request(url, callback=self.parse,
                              meta={'params': params})
        for genre in genres:
            params = self.params.copy()
            params['q'] = genre
            url = '{}?{}'.format(self.api_url, up.urlencode(params))
            yield Request(url, callback=self.parse,
                          meta={'params': params})

    def parse(self, response):
        if response.status != 200:
            request = response.request.copy()
            request.dont_filter = True
            return request
        data = json.loads(response.text)
        if len(data['data']) > 0:
            params = response.request.meta['params']
            params['start'] += self.offset
            url = '{}?{}'.format(self.api_url, up.urlencode(params))
            yield Request(url, callback=self.parse, meta={'params': params})
        skipped = 0
        for d in data['data']:
            _id = d['id']
            if self.is_duplicated_item(_id):
                skipped += 1
                continue
            params = self.detail_params
            url = '{}/{}?{}'.format(self.detail_api_url, _id,
                                    up.urlencode(params))
            yield Request(url, callback=self.parse_item,
                          meta={'data': d}, priority=1)
        self.logger.info(
            'Craped {} items, Skipped {} items'.format(
                len(data['data']), skipped))

    def parse_item(self, response):
        if response.status != 200:
            request = response.request.copy()
            request.dont_filter = True
            return request
        meta_data = response.request.meta['data']
        meta_data.update(json.loads(response.text))
        item = MovieItem()
        item['_id'] = meta_data['id']
        item['url'] = meta_data['url']
        item['title'] = meta_data['title']
        item['rate'] = meta_data['rating']['value']
        item['directors'] = [d['name'] for d in meta_data['directors']]
        item['casts'] = [d['name'] for d in meta_data['actors']]
        item['genres'] = meta_data['genres']
        item['source'] = meta_data['countries']
        item['lang'] = meta_data['languages']
        item['release_date'] = meta_data['pubdate']
        item['runtime'] = meta_data['durations']
        item['aliases'] = meta_data['aka']
        item['summary'] = meta_data['intro']
        yield item
