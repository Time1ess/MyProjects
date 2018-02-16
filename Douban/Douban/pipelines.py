# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo

from bson.objectid import ObjectId
from scrapy.exceptions import DropItem

from Douban.settings import MONGO_HOST, MONGO_PORT, MONGO_DB
from Douban.spiders.Movie import MovieSpider, MMovieSpider
from Douban.items import MovieItem


class MoviePipeline(object):
    COLLECTION_NAME = 'Movies'

    def open_spider(self, spider):
        if not isinstance(spider, (MovieSpider, MMovieSpider)):
            return
        self.client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        self.db = self.client[MONGO_DB]
        self.collection = self.db[self.COLLECTION_NAME]

    def process_item(self, item, spider):
        if not isinstance(item, MovieItem):
            return item
        data = dict(item)
        if self.collection.find_one({'_id': data['_id']}) is not None:
            raise DropItem('Already processed {}'.format(item))
        self.collection.insert_one(data)
        return item
