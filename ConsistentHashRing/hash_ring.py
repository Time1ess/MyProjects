import bisect

from string import ascii_letters
from random import choices, randint
from hashlib import md5


class CHashRing:
    """Consistent Hash Ring."""
    def __init__(self, nodes, replicas=3):
        self._sorted_keys = []
        self._replicas = replicas
        self._keys = {}
        for node in nodes:
            self.add_node(node)

    def add_node(self, node):
        for idx in range(self._replicas):
            key = self.hash('%s:%d' % (node, idx))
            self._keys[key] = node
            self._sorted_keys.append(key)
        self._sorted_keys.sort()

    def remove_node(self, node):
        for idx in range(self._replicas):
            key = self.hash('%s:%d' % (node, idx))
            self._keys.pop(key)
            self._sorted_keys.remove(key)

    def get_node(self, val):
        if not self._sorted_keys:
            return None
        key = self.hash(val)
        pos = bisect.bisect_left(self._sorted_keys, key)
        if pos == len(self._sorted_keys):
            pos = 0
        return self._keys[self._sorted_keys[pos]]

    def hash(self, val):
        h = md5()
        h.update(val.encode())
        return int(h.hexdigest(), base=16) % (2**32)


ring = CHashRing([
    '192.168.1.5',
    '192.168.1.53',
    '192.168.1.127',
    '192.168.1.66',
    '192.168.1.39',
    ], replicas=150)
cnts = {}
for _ in range(100000):
    val = ''.join(choices(ascii_letters, k=randint(10, 100)))
    node = ring.get_node(val)
    cnts.setdefault(node, 0)
    cnts[node] += 1
print(cnts)
