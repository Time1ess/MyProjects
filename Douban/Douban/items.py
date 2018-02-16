# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MovieItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    rate = scrapy.Field()
    directors = scrapy.Field()
    casts = scrapy.Field()
    genres = scrapy.Field()
    source = scrapy.Field()
    lang = scrapy.Field()
    release_date = scrapy.Field()
    runtime = scrapy.Field()
    aliases = scrapy.Field()
    summary = scrapy.Field()
