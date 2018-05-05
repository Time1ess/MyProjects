import sys

from time import time as now


class RateLimiter(object):
    bucket = {}

    def __init__(self, qps=5):
        self.qps = qps

    def access(self, host, token=1, *args, **kwargs):
        if self.can_access(host, token):
            return True
        return False

    def can_access(self, host, token):
        host_data = self.bucket.setdefault(host, [now(), 0])
        t = now()
        more_tokens = (t - host_data[0]) / (1 / self.qps)
        if more_tokens >= 1:
            host_data[1] = min(more_tokens + host_data[1], token)
            host_data[0] = t
        if host_data[1] >= token:
            host_data[1] -= token
            return True
        else:
            return False


def main():
    rate = 100
    rl = RateLimiter(rate)
    start = now()
    cnt = 0
    max_qps = 0
    while True:
        if rl.access('localhost', 200):
            cnt += 1
        t = now()
        qps = cnt / (t - start)
        max_qps = max(qps, max_qps)
        sys.stdout.flush()
        sys.stdout.write('QPS:{:010.2f} MAX_QPS:{:010.2f}\r'.format(
            qps, max_qps))


if __name__ == '__main__':
    main()
