import string
import time
import redis


conn = redis.Redis(decode_responses=True)
CNT_KEY = 'TINY_URL_CNT'
valid_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits


def tiny_url_hash(tiny_id, hash_len=7):
    """Convert a ID into a tiny URL."""
    tiny_url = ''
    while tiny_id:
        tiny_url += (valid_chars[tiny_id % len(valid_chars)])
        tiny_id = tiny_id // len(valid_chars)
    tiny_url = (hash_len - len(tiny_url)) * valid_chars[0] + tiny_url
    return tiny_url


def insert(url):
    """Convert a url to a tiny url."""
    pipe = conn.pipeline()
    end = time.time() + 10
    while time.time() < end:
        try:
            pipe.watch(CNT_KEY)
            cnt = pipe.get(CNT_KEY) or 0
            tiny_url = tiny_url_hash(int(cnt))
            pipe.multi()
            pipe.set(tiny_url, url)
            pipe.incr(CNT_KEY)
            pipe.execute()
            return tiny_url
        except redis.exceptions.WatchError:
            pass
    return None


def parse(tiny_url):
    """Convert a tiny url to a url."""
    return conn.get(tiny_url)


def test():
    with open('URLs.txt', 'r') as f:
        urls = [line.strip() for line in f]
    for size in (int(10**x) for x in range(1, 7)):
        chunk_urls = urls[:size]
        conn.flushdb()
        s = time.time()
        res = [parse(insert(url)) == url for url in chunk_urls]
        assert all(res) == True
        e = time.time()
        print('Count: {:7d}, Total: {:.3f}, Avg: {:.9f}, IPS: {:6d}'.format(
            size, e-s, (e-s) / size, int(size / (e-s))))



if __name__ == '__main__':
    test()
