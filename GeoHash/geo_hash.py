import matplotlib.pyplot as plt
from PIL import Image


def b32_encode(x_bin):
    b32_chars = '0123456789bcdefghjkmnpqrstuvwxyz'
    start_indices = (i for i in range(0, len(x_bin), 5))
    return ''.join(b32_chars[int(x_bin[i:i+5], base=2)] for i in start_indices)


def geo_hash(lon, lat, p=6, return_all=False):
    min_lon, max_lon = -180, 180
    min_lat, max_lat = -90, 90
    ans = 0
    is_lon = True
    bits = p * 5
    while bits > 0:
        ans = ans << 1
        if is_lon:
            m = min_lon + (max_lon - min_lon) / 2
            if lon < m:
                max_lon = m
            else:
                ans = ans | 1
                min_lon = m
        else:
            m = min_lat + (max_lat - min_lat) / 2
            if lat < m:
                max_lat = m
            else:
                ans = ans | 1
                min_lat = m
        is_lon = not is_lon
        bits -= 1
    ans = bin(ans)[2:]
    if return_all:
        return b32_encode(ans), min_lat, max_lat, min_lon, max_lon
    return b32_encode(ans)


def geo_hash_range(lon, lat, p=6):
    _, min_lat, max_lat, min_lon, max_lon = geo_hash(lon, lat, p, True)
    return min_lat, max_lat, min_lon, max_lon


class Converter:
    def __init__(self, min_lat, max_lat, min_lon, max_lon, max_x, max_y):
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lon = min_lon
        self.max_lon = max_lon
        self.max_x = max_x
        self.max_y = max_y

    def lon_to_x(self, lon):
        x = self.max_x
        minl, maxl = self.min_lon, self.max_lon
        if lon == minl:
            return x
        else:
            return int(round(x * (lon - minl) / (maxl - minl)))

    def lat_to_y(self, lat):
        y = self.max_y
        minl, maxl = self.min_lat, self.max_lat
        if lat == minl:
            return y
        else:
            return int(round(y * (lat - minl) / (maxl - minl)))


img = Image.open('src.png')
plt.figure(figsize=(16, 16))
plt.imshow(img)
X, Y = img.size

with open('coords.txt') as f:
    left_top, right_bottom = [x.strip().split(' ') for x in f.readlines()]

left_top = [float(x) for x in left_top]
right_bottom = [float(x) for x in right_bottom]
MIN_LAT, MAX_LON = right_bottom[1], right_bottom[0]
MAX_LAT, MIN_LON = left_top[1], left_top[0]
for P, (fc, lc) in zip([6, 6], [('red', 'blue'), ('blue', 'green')]):
    conv = Converter(MIN_LAT, MAX_LAT, MIN_LON, MAX_LON, X, Y)
    lat = MIN_LAT
    while lat < MAX_LAT:
        lon = MIN_LON
        while lon < MAX_LON:
            min_lat, max_lat, min_lon, max_lon = geo_hash_range(lon, lat, P)
            minx = conv.lon_to_x(min_lon)
            maxx = conv.lon_to_x(max_lon)
            miny = conv.lat_to_y(min_lat)
            maxy = conv.lat_to_y(max_lat)
            lon = max_lon
            cx = (minx + maxx) / 2
            clon = (min_lon + max_lon) / 2
            clat = (min_lat + max_lat) / 2
            cy = (miny + maxy) / 2
            # t = '{}\n{}\n{}'.format(geo_hash(clon, clat, P), clon, clat)
            t = geo_hash(clon, clat, P)
            plt.text(cx - 70, cy, t, color=fc,
                     fontsize=(1/P)**2 * 300)
            plt.plot([minx, minx, maxx, maxx, minx],
                     [miny, maxy, maxy, miny, miny],
                     c=lc)
            if maxx > X:
                break
        min_lat, max_lat, min_lon, max_lon = geo_hash_range(MIN_LON, lat, P)
        lat = max_lat
        miny = conv.lat_to_y(min_lat)
        maxy = conv.lat_to_y(max_lat)
        minx = conv.lon_to_x(min_lon)
        maxx = conv.lon_to_x(max_lon)
        if maxy > Y:
            break

plt.show()
