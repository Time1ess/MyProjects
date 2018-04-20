REDIS_HOST = 'localhost'
REDIS_PORT = 6379
DECODE_RESPONSE = True

USER_TWEETS_KEY_FMT = 'tweets:%s'
TIMELINE_KEY_FMT = 'timeline:%s'
TWEET_KEY_FMT = 'tweet:%s'
FOLLOWERS_KEY_FMT = 'followers:%s'
FOLLOWEES_KEY_FMT = 'followees:%s'


MAX_LIMIT = 100
DEFAULT_LIMIT = 20

# Threshold for directly inserting tweets to followers' timeline
# > this thres, perform delay insertion
# < this thres, perform direct insertion
DIRECT_INSERT_THRES = 200
