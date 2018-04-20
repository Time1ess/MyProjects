import string
import random
import contextlib

from time import process_time


from core import conn
from users import follow
from tweets import post_tweet


def create_connections(N, M, K1=None, K2=None):
    """Create connections from users 1 - N.

    Users with uid less equal than M will be considered as celebrities
    having many followers.
    
    Parameters
    ----------
    N: int
        The number of users.
    M: int
        The number of celebrities.
    K1: int
        The average number of followers for celebrities. Default: 0.05 * N.
    K2: int
        The average number of followers for normal users. Default: 0.001 * N.
    """
    assert N >= M
    if K1 is None:
        K1 = int(N * 0.05)
    if K2 is None:
        K2 = int(N * 0.001)
    for uid in range(1, M + 1):
        pipe = conn.pipeline(False)
        s = random.randint(1, N - K1)
        for follower_uid in range(s, s + K1):
            follow(follower_uid, uid, pipe)
        pipe.execute()
    for uid in range(M + 1, N + 1):
        pipe = conn.pipeline(False)
        s = random.randint(1, N - K2)
        for follower_uid in range(s, s + K2):
            follow(follower_uid, uid, pipe)
        pipe.execute()


def fake_tweet_body(K=120):
    return ''.join(random.choices(string.ascii_letters,
                                  k=random.randint(10, K)))


def fake_location():
    return random.choice([
        'Dalian', 'Chengdu', 'Hangzhou', 'Beijing', 'Shenzheng', 'Shanghai',
        'Shenyang', 'Deyang', 'Mianzhu', 'Chongqin', 'Henan', 'Haerbin',
        'Jilin', 'Suzhou', 'Nanjing', 'New York', 'Canada', 'UK', 'Russia',
    ])


def create_tweets(N, M, K1=200, K2=80):
    """Create tweets from users 1 - N.

    Users with uid less equal than M will be considered as celebrities
    having many followers.
    """
    assert N >= M
    pipe = conn.pipeline(False)
    for uid in range(1, M + 1):
        pipe = conn.pipeline(False)
        for _ in range(K1):
            post_tweet(uid, pipe, body=fake_tweet_body(),
                       location=fake_location())
        pipe.execute()
    for uid in range(M + 1, N + 1):
        pipe = conn.pipeline(False)
        for _ in range(K2):
            post_tweet(uid, pipe, body=fake_tweet_body(),
                       location=fake_location())
        pipe.execute()


@contextlib.contextmanager
def timeit():
    s = process_time()
    yield
    e = process_time()
    print('Process Time: {:.4f}'.format(e-s))


if __name__ == '__main__':
    pass
