# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class UserProfile(scrapy.Item):
    _id = scrapy.Field()

    # Profile
    name = scrapy.Field()
    headline = scrapy.Field()
    gender = scrapy.Field()
    locations = scrapy.Field()
    business = scrapy.Field()
    employments = scrapy.Field()
    educations = scrapy.Field()
    description = scrapy.Field()

    # Achievements
    voteup_cnt = scrapy.Field()
    thanked_cnt = scrapy.Field()
    favorited_cnt = scrapy.Field()

    # Activities
    answer_cnt = scrapy.Field()
    question_cnt = scrapy.Field()
    article_cnt = scrapy.Field()
    column_cnt = scrapy.Field()
    pin_cnt = scrapy.Field()
    favorite_cnt = scrapy.Field()
    hosted_live_cnt = scrapy.Field()
    participated_live_cnt = scrapy.Field()
    following_topic_cnt = scrapy.Field()
    following_column_cnt = scrapy.Field()
    following_question_cnt = scrapy.Field()
    following_question_cnt = scrapy.Field()
    following_fav_list_cnt = scrapy.Field()

    # Relationships
    follower_cnt = scrapy.Field()
    following_cnt = scrapy.Field()
    followers = scrapy.Field()  # Set by FollowRelationShip
    followings = scrapy.Field()  # Set by FollowRelationShip

    status = scrapy.Field()


class FollowRelationShip(scrapy.Item):
    user_id = scrapy.Field()
    following_id = scrapy.Field()
