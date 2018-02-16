# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
import random

import requests

from scrapy import signals
from scrapy.exceptions import CloseSpider

from twisted.internet import reactor
from twisted.internet.defer import Deferred

from Zhihu.agents import AGENTS


class RandomUserAgentMiddleware(object):
    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        #agent = random.choice(AGENTS)
        agent = AGENTS[0]
        request.headers['User-Agent'] = agent


class ProxyMiddleware():
    def process_request(self, request, spider):
        proxy = requests.get('http://localhost:5000/api/proxy').json()['proxy']
        request.meta['proxy'] = proxy


class SleepMiddleware():
    sleep_time = 300

    def process_response(self, request, response, spider):
        engine = spider.crawler.engine

        def _resume():
            spider.logger.info('Spider resumed: %s' % spider.name)
            engine.unpause()

        if 400 < response.status < 500:
            spider.logger.info('Spider paused(throttle): %s' % spider.name)
            engine.pause()
            reactor.callLater(self.sleep_time, _resume)
            return request
        else:
            return response
