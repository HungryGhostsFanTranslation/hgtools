"""
I'm hoping eventually I can just do this programmatically but I don't currently have
enough examples so I just hardcode the pattern(s) in this file.
"""

scramble_patterns = {
    # 256 x 64 aka 128 x 128
    "256_64": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(3, 0), (3, 1), (3, 2), (3, 3)],
        [(4, 0), (4, 1), (4, 2), (4, 3)],
        [(5, 0), (5, 1), (5, 2), (5, 3)],
        [(6, 0), (6, 1), (6, 2), (6, 3)],
        [(7, 0), (7, 1), (7, 2), (7, 3)]
    ],
    # 512 x 128 aka 256 x 256
    "512_128": [
        [(0, 0), (0, 1), (0, 2), (0, 3), (8, 0), (8, 1), (8, 2), (8, 3)],
        [(1, 0), (1, 1), (1, 2), (1, 3), (9, 0), (9, 1), (9, 2), (9, 3)],
        [(2, 0), (2, 1), (2, 2), (2, 3), (10, 0), (10, 1), (10, 2), (10, 3)],
        [(3, 0), (3, 1), (3, 2), (3, 3), (11, 0), (11, 1), (11, 2), (11, 3)],
        [(4, 0), (4, 1), (4, 2), (4, 3), (12, 0), (12, 1), (12, 2), (12, 3)],
        [(5, 0), (5, 1), (5, 2), (5, 3), (13, 0), (13, 1), (13, 2), (13, 3)],
        [(6, 0), (6, 1), (6, 2), (6, 3), (14, 0), (14, 1), (14, 2), (14, 3)],
        [(7, 0), (7, 1), (7, 2), (7, 3), (15, 0), (15, 1), (15, 2), (15, 3)],
        [(0, 4), (0, 5), (0, 6), (0, 7), (8, 4), (8, 5), (8, 6), (8, 7)],
        [(1, 4), (1, 5), (1, 6), (1, 7), (9, 4), (9, 5), (9, 6), (9, 7)],
        [(2, 4), (2, 5), (2, 6), (2, 7), (10, 4), (10, 5), (10, 6), (10, 7)],
        [(3, 4), (3, 5), (3, 6), (3, 7), (11, 4), (11, 5), (11, 6), (11, 7)],
        [(4, 4), (4, 5), (4, 6), (4, 7), (12, 4), (12, 5), (12, 6), (12, 7)],
        [(5, 4), (5, 5), (5, 6), (5, 7), (13, 4), (13, 5), (13, 6), (13, 7)],
        [(6, 4), (6, 5), (6, 6), (6, 7), (14, 4), (14, 5), (14, 6), (14, 7)],
        [(7, 4), (7, 5), (7, 6), (7, 7), (15, 4), (15, 5), (15, 6), (15, 7)],
    ],
    "256_128": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(3, 0), (3, 1), (3, 2), (3, 3)],
        [(4, 0), (4, 1), (4, 2), (4, 3)],
        [(5, 0), (5, 1), (5, 2), (5, 3)],
        [(6, 0), (6, 1), (6, 2), (6, 3)],
        [(7, 0), (7, 1), (7, 2), (7, 3)],
        [(0, 4), (0, 5), (0, 6), (0, 7)],
        [(1, 4), (1, 5), (1, 6), (1, 7)],
        [(2, 4), (2, 5), (2, 6), (2, 7)],
        [(3, 4), (3, 5), (3, 6), (3, 7)],
        [(4, 4), (4, 5), (4, 6), (4, 7)],
        [(5, 4), (5, 5), (5, 6), (5, 7)],
        [(6, 4), (6, 5), (6, 6), (6, 7)],
        [(7, 4), (7, 5), (7, 6), (7, 7)],
    ],
    "64_64": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "64_16": [[(0, 0)], [(1, 0)]]
}
