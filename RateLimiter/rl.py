import sys

from time import time as now


class RateLimiter(object):
    bucket = {}
    def __init__(self, rate=5):
        self.rate = rate

    def access(self, host, *args, **kwargs):
        if self.can_access(host):
            return True
        return False

    def can_access(self, host):
        host_data = self.bucket.setdefault(host, [now(), 1])
        t = now()
        more_tokens = (t - host_data[0]) / (1 / self.rate)
        if more_tokens > 0:
            host_data[1] = min(more_tokens + host_data[1], self.rate)
            host_data[0] = t
        if host_data[1] > 1:
            host_data[1] -= 1
            return True
        else:
            return False


def main():
    rl = RateLimiter(100)
    start = now()
    cnt = 0
    while True:
        if rl.access('localhost'):
            cnt += 1
        sys.stdout.flush()
        sys.stdout.write('{:10d}\r'.format(int(cnt/(now() - start))))


if __name__ == '__main__':
    main()
