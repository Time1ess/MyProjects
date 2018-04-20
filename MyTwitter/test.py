import config


from test_utils import (
    create_connections, create_tweets, timeit,
    fake_tweet_body, fake_location)

from tweets import post_tweet
from users import get_timeline


# N = int(1e4)
# M = int(1e2)
# 
# print('Create connections')
# with timeit():
#     create_connections(N, M)
# 
# print('Create tweets')
# with timeit():
#     create_tweets(N, M)


print('Celebrity create a new tweet with delay insertion')
with timeit():
    repeat_times = 100
    for _ in range(repeat_times):
        post_tweet('2', body=fake_tweet_body(), location=fake_location())


print('Normal user create a new tweet with direct insertion')
with timeit():
    repeat_times = 100
    for _ in range(repeat_times):
        post_tweet('1001', body=fake_tweet_body(), location=fake_location())


print('Celebrity timeline')
with timeit():
    repeat_times = 50
    for uid in range(1, repeat_times + 1):
        get_timeline(uid)

print('Normal timeline')
with timeit():
    repeat_times = 50 
    for uid in range(500, repeat_times + 1):
        get_timeline(uid)


config.DIRECT_INSERT_THRES = 10000
print('\nAll with direct insertion.\n')

print('Celebrity create a new tweet with direct insertion')
with timeit():
    repeat_times = 100
    for _ in range(repeat_times):
        post_tweet('2', body=fake_tweet_body(), location=fake_location())


print('Normal user create a new tweet with direct insertion')
with timeit():
    repeat_times = 1000
    for _ in range(repeat_times):
        post_tweet('1001', body=fake_tweet_body(), location=fake_location())


print('Celebrity timeline')
with timeit():
    repeat_times = 50
    for uid in range(51, repeat_times + 1):
        get_timeline(uid)

print('Normal timeline')
with timeit():
    repeat_times = 50
    for uid in range(551, repeat_times + 1):
        get_timeline(uid)
