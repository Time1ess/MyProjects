import utils
import config
import tweets

from core import conn


def get_followers(uid):
    """Return all ids of users who are following a specified user."""
    return conn.zrange(utils.get_followers_key(uid), 0, -1)


def get_followers_count(uid):
    """Return the number of users who are following a specified user."""
    return conn.zcard(utils.get_followers_key(uid))


def get_followees(uid):
    """Return all ids of users who are followed by a specified user."""
    return conn.zrange(utils.get_followees_key(uid), 0, -1)


def get_followees_count(uid):
    """Return the number of users who are followed a specified user."""
    return conn.zcard(utils.get_followees_key(uid))


def follow(follower, followee, pipe=None):
    """Create a connection between follower and followee."""
    if pipe is None:
        pipe = conn.pipeline()
        execute = True
    else:
        execute = False
    pipe.zadd(utils.get_followers_key(followee),
              follower, utils.get_timestamp())
    pipe.zadd(utils.get_followees_key(follower),
              followee, utils.get_timestamp())
    if execute:
        pipe.execute()


def unfollow(follower, followee):
    """Remove a connection between follower and followee."""
    follow_ts = conn.zscore(utils.get_followers_key(followee), follower)
    _tweets = tweets.get_tweets_since(followee, follow_ts, {'tid', 'uid'})
    pipe = conn.pipeline()
    pipe.zrem(utils.get_followers_key(followee), follower)
    pipe.zrem(utils.get_followees_key(follower), followee)
    tweets.delete_tweets(_tweets, pipe)
    pipe.execute()


def get_user_tweets(uid, limit=None, offset=0):
    """Return specified user tweets limited by limit and offset."""
    if limit is None:
        limit = config.DEFAULT_LIMIT
    else:
        limit = min(config.MAX_LIMIT, limit)
    tids = conn.zrange(utils.get_user_tweets_key(uid),
                       offset, offset + limit - 1)
    return tweets.get_tweets(tids)


def get_timeline(uid, limit=None, offset=0):
    """Return sepcified user timeline limited by limit and offset."""
    if limit is None:
        limit = config.DEFAULT_LIMIT
    else:
        limit = min(config.MAX_LIMIT, limit)
    refresh_timeline(uid)
    tids = conn.zrevrange(utils.get_timeline_key(uid),
                          offset, offset + limit - 1)
    return tweets.get_tweets(tids)


def refresh_timeline(uid):
    """Refresh user's timeline.

    Fetch all delayed tweets from his/her followees.
    """
    last_tid = conn.zrevrange(utils.get_timeline_key(uid), 0, 0)
    last_tweet = tweets.get_tweet(last_tid)
    if not last_tweet:
        return
    followees = get_followees(uid)
    pipe = conn.pipeline(False)
    for followee in followees:
        _tweets = tweets.get_tweets_since(followee, last_tweet.ts,
                                          {'tid', 'datetime'})
        for tweet in _tweets:
            pipe.zadd(utils.get_timeline_key(uid), tweet.tid, tweet.ts)
    pipe.execute()


if __name__ == '__main__':
    print(len(get_user_tweets('1')))
    # print(get_timeline('1'))
