from uuid import uuid4
from datetime import datetime

import utils
import config
import users

from core import conn
from model import Tweet


def post_tweet(uid, pipe=None, **tweet_info):
    """Create a new tweet with basic infomation.

    Parameters
    ----------
    uid: str
        User ID.
    pipe: Pipeline object
        A Redis pipeline object, if given, need to execute manually outside
        this function.
    body: str
        The body of the tweet.
    location: str
        The location when posting this tweet.
    original: bool
        Whether this tweet is an original tweet or just a retweet.
    """
    tweet_info['uid'] = uid
    tweet_info['tid'] = uuid4().hex
    tweet_info['datetime'] = datetime.now()
    tweet_info.setdefault('original', True)
    tweet = Tweet.load_dict(tweet_info)
    if pipe is None:
        pipe = conn.pipeline(False)
        execute = True
    else:
        execute = False
    pipe.hmset(utils.get_tweet_key(tweet.tid), tweet.dump_dict())
    pipe.zadd(utils.get_user_tweets_key(uid), tweet.tid, tweet.ts)
    pipe.zadd(utils.get_timeline_key(uid), tweet.tid, tweet.ts)
    if users.get_followers_count(uid) < config.DIRECT_INSERT_THRES:
        # Perform direct insertion
        followers = users.get_followers(uid)
        for follower_uid in followers:
            pipe.zadd(utils.get_timeline_key(follower_uid),
                      tweet.tid, tweet.ts)
    if execute:
        pipe.execute()


def get_tweet(tid):
    """Return a tweet with specified tid."""
    return Tweet.load_dict(conn.hgetall(utils.get_tweet_key(tid)))


def get_tweets(tids, fields=None):
    """Return tweets with specified tids."""
    pipe = conn.pipeline(False)
    for tid in tids:
        if fields is None:
            pipe.hgetall(utils.get_tweet_key(tid))
        else:
            pipe.hmget(utils.get_tweet_key(tid), *fields)
    tweets = [Tweet.load_dict(d) for d in pipe.execute()]
    return tweets


def get_tweets_since(uid, since, fields=None):
    """Return tweets of a specified user since a specified time."""
    tids = conn.zrevrangebyscore(utils.get_user_tweets_key(uid), 'inf', since)
    if fields is not None:
        return get_tweets(tids, fields)
    return tids


def delete_tweet_with_tid(tid, pipe=None):
    """Delete a tweet with specified tid."""
    delete_tweet(get_tweet(tid), pipe)


def delete_tweet(tweet, pipe=None):
    """Delete a tweet."""
    followers = users.get_followers(tweet.uid)
    if pipe is None:
        pipe = conn.pipeline(False)
        execute = True
    else:
        execute = False
    pipe.zrem(utils.get_user_tweets_key(tweet.uid), tweet.tid)
    pipe.zrem(utils.get_timeline_key(tweet.uid), tweet.tid)
    for follower_uid in followers:
        pipe.zrem(utils.get_timeline_key(follower_uid), tweet.tid)
    pipe.delete(utils.get_tweet_key(tweet.tid))
    if execute:
        pipe.execute()


def delete_tweets(tweets, pipe=None):
    """Delete tweets with specified tids."""
    execute = True
    if pipe is None:
        pipe = conn.pipeline(False)
        execute = True
    else:
        execute = False
    for tweet in tweets:
        delete_tweet(tweet, pipe)
    if execute:
        pipe.execute()


if __name__ == '__main__':
    pass
