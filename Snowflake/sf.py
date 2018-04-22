from time import time
from random import getrandbits


class Snowflake:
    """Distributed ID generation algorithm by Twitter."""
    def __init__(self, data_center_id, worker_id):
        assert data_center_id < 32 and worker_id < 32
        self.data_center_id = data_center_id
        self.worker_id = worker_id
        self.ms = 0
        self.sqn = 0

    @staticmethod
    def get_ts():
        return int(time() * 1000)

    def gen_id(self):
        """Generate universally unique ID.

        0 - 00000 00000 00000 00000 00000 00000 00000 00000 0 - 00000 - 00000 - 00000 00000 00

        From left to right:
        0 bit: Reserved.
        1 - 41 bits: Timestamp in millisecond.
        42 - 46 bits: Data center ID.
        47 - 51 bits: Worker ID.
        52 - 63 bits: Sequence number in one millisecond.
        """
        uid = 0
        ms = self.get_ts()
        full = False
        if self.sqn == 4096:
            # Wait until next millisecond
            while ms == self.ms:
                ms = self.get_ts()
            full = True
        if self.ms <= ms or full:
            self.sqn = getrandbits(14)
        self.ms = ms
        uid = uid | (ms << 22)  # Timestamp
        uid = uid | (self.data_center_id << 17)  # Data center ID
        uid = uid | (self.worker_id << 12)  # Worker ID
        uid = uid | self.sqn
        self.sqn += 1
        return uid


sf = Snowflake(1, 2)
N = 100000
s = time()
for _ in range(N):
    sf.gen_id()
e = time()
print('IDs per second:', int(N / (e-s)), 'Id/ms:', 1000 * (e-s)/N)
