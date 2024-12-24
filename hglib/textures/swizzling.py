import math
from os import makedirs
from os.path import isdir, join, expanduser

from diskcache import Cache
home_dir = expanduser("~")
cache_dir = join(home_dir, ".local", "share", "hgtools", "swizzling")
cache = Cache(cache_dir)

        

def unswizzle_8bpp(x, y):
    x0 = x & 0x80
    x1 = x & 0x40
    x2 = x & 0x20
    x3 = x & 0x10
    x4 = x & 0x08
    x5 = x & 0x04
    x6 = x & 0x02
    x7 = x & 0x01
    x3_flag = x3 >> 4
    y2_flag = (y & 0x02) >> 1
    fill_order = x3_flag ^ y2_flag
    low_bits = (x4 >> 2) | (x5 >> 2) | (x6 << 2) | ((x7 ^ fill_order) << 2)
    pixel_x = (x >> 5) << 4 | low_bits
    pixel_y = ((y & 0xFFFFFE) << 1) | (x7 << 1) | (y & 0x01)

    if y >= 100 and pixel_y == 0:
        import sys

        sys.exit("Uh oh: (%s, %s)" % (x, y))

    return pixel_x, pixel_y


def unswizzle_4bpp(x, y):
    x0 = x & 0x80
    x1 = x & 0x40
    x2 = x & 0x20
    x3 = x & 0x10
    x4 = x & 0x08
    x5 = x & 0x04
    x6 = x & 0x02
    x7 = x & 0x01
    x2_flag = x2 >> 5
    x3_flag = x3 >> 3
    y2_flag = (y & 0x02) >> 1
    y4_flag = (y & 0x08) >> 3
    y5_flag = (y & 0x10) >> 4

    fill_order = x2_flag ^ y2_flag
    low_bits = (
        (x4 >> 3) | (x3 >> 3) | ((x7 ^ 0x1) ^ fill_order) << 2 | (x5 << 2) | (x6 << 2) | y4_flag << 5 | y5_flag << 6
    )
    pixel_x = low_bits | (x&0x200) >> 2 | (x&0x400) >> 2
    pixel_y =  (y&0xffe0) << 2 | ((y & 0x6) << 1) | ((x7 ^ 0x1) << 1) | (y & 0x01) | x1 >> 2 | x0 >> 2 | (x&0x100) >> 2
    return pixel_x, pixel_y


def get_maps_8bpp(img_width, img_height):
    if f"{img_width}||{img_height}" in cache:
        return cache[f"{img_width}||{img_height}"]
    swizzle_map = [[(None, None) for _ in range(img_width)] for _ in range(img_height)]
    deswizzle_map = [
        [(None, None) for _ in range(int(img_width * 2))]
        for _ in range(int(img_height / 2))
    ]
    for x in range(0, int(img_width * 2)):
        for y in range(0, int(img_height / 2)):
            unswizzled_x, unswizzled_y = unswizzle_8bpp(x, y)
            deswizzle_map[y][x] = (unswizzled_x, unswizzled_y)
            swizzle_map[unswizzled_y][unswizzled_x] = (x, y)

    cache[f"{img_width}||{img_height}"] = (swizzle_map, deswizzle_map)
    return (swizzle_map, deswizzle_map)


def get_maps_4bpp(img_width, img_height):
    if f"{img_width}||{img_height}" in cache:
        return cache[f"{img_width}||{img_height}"]
    swizzle_map = [[(None, None) for _ in range(img_width)] for _ in range(img_height*8)]
    deswizzle_map = [
        [(None, None) for _ in range(int(img_width * 2))]
        for _ in range(int(img_height *2))
    ]
    for x in range(0, int(img_width * 2)):
        for y in range(0, int(img_height)):
            unswizzled_x, unswizzled_y = unswizzle_4bpp(x, y)
            deswizzle_map[y][x] = (unswizzled_x, unswizzled_y)
            swizzle_map[unswizzled_y][unswizzled_x] = (x, y)
    cache[f"{img_width}||{img_height}"] = (swizzle_map, deswizzle_map)
    return (swizzle_map, deswizzle_map)


def unswizzle(x, y, deswizzle_map):
    real_x, real_y = deswizzle_map[y][x]
    return real_x, real_y


def swizzle(x, y, swizzle_map):
    swizzled_x, swizzled_y = swizzle_map[y][x]
    return swizzled_x, swizzled_y
