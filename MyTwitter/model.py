class Tweet(object):
    __slots__ = {'uid', 'tid', 'body', 'location', 'datetime', 'original'}

    @classmethod
    def load_dict(cls, raw_data):
        if not raw_data:
            return None
        inst = cls()
        for k in cls.__slots__:
            if k in raw_data:
                setattr(inst, k, raw_data[k])
        return inst

    @property
    def ts(self):
        return self.datetime.timestamp()

    def dump_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}

    def __str__(self):
        return 'Tweet:' + self.uid + '-' + self.tid

    def __repr__(self):
        return '<Tweet uid:{} tid:{}>'.format(self. uid, self.tid)


if __name__ == '__main__':
    tweet = Tweet.load_dict({
        'uid': '1', 'tid': '1233',
        'body': 'Hello World', 'location': 'NY',
        'datetime': 'fake dt', 'original': True})
    print(tweet)
    print(tweet.dump_dict())
