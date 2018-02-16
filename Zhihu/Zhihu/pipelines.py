# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo

from scrapy.exceptions import DropItem

from Zhihu.settings import MONGO_HOST, MONGO_PORT, MONGO_DB
from Zhihu.items import UserProfile, FollowRelationShip


class UserProfilePipeline(object):
    COLLECTION_NAME = 'profiles'

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        self.db = self.client[MONGO_DB]
        self.collection = self.db[self.COLLECTION_NAME]

    def process_item(self, item, spider):
        if not isinstance(item, UserProfile):
            return item
        data = dict(item)
        _id = data['_id']
        if self.collection.find_one({'_id': _id, 'status': 1}) is not None:
            raise DropItem('DropItem: {}'.format(_id))
        self.collection.update_one({'_id': _id}, {'$set': data}, upsert=True)
        return item


class FollowRelationShipPipeline(object):
    COLLECTION_NAME = 'profiles'

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        self.db = self.client[MONGO_DB]
        self.collection = self.db[self.COLLECTION_NAME]

    def get_or_create(self, _id):
        data = self.collection.find_one({'_id': _id})
        if data is None:
            data = UserProfile({'_id': _id})
            self.collection.insert_one(dict(data))
        return data

    def process_item(self, item, spider):
        if not isinstance(item, FollowRelationShip):
            return item
        user_id = item['user_id']
        following_id = item['following_id']
        if self.collection.find_one({'_id': user_id}) is None:
            self.collection.insert_one({'_id': user_id, 'followings': {}})
        self.collection.update_one(
            {'_id': user_id},
            {'$set': {'following.{}'.format(following_id): ''}}, upsert=True)
        if self.collection.find_one({'_id': following_id}) is None:
            self.collection.insert_one({'_id': following_id, 'followers': {}})
        self.collection.update_one(
            {'_id': following_id},
            {'$set': {'followers.{}'.format(user_id): ''}}, upsert=True)
        return item
