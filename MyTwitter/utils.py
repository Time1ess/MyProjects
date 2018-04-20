from datetime import datetime


import config


def get_user_tweets_key(uid):
    return config.USER_TWEETS_KEY_FMT % uid


def get_timeline_key(uid):
    return config.TIMELINE_KEY_FMT % uid


def get_tweet_key(tid):
    return config.TWEET_KEY_FMT % tid


def get_followers_key(uid):
    return config.FOLLOWERS_KEY_FMT % uid


def get_followees_key(uid):
    return config.FOLLOWEES_KEY_FMT % uid


def get_timestamp():
    return datetime.now().timestamp()
