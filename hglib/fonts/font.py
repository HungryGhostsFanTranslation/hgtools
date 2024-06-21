"""
Code for patching the game's two font files. 
"""
import math
import sys
import numpy as np
import png
from itertools import batched


masks = [0x11, 0x22, 0x44, 0x88]


class Font:
    def __init__(
        self, filename: str, title: str, width: int, height: int, interleaved: bool
    ):
        self.filename = filename

        self.title = title
        self.width = width
        self.height = height
        self.interleaved = interleaved
        self.tiles = []
        self.read()

    def read(self):
        """
        Parse a binary font file. Font files are bitmasked 1bpp, with each byte
        containing data for four 24x24px tiles. 
        
        The variable-width font stores 2 12x24 characters stacked vertically. Every
        other row is interleaved which requires special code to handle.
        """

        with open(self.filename, "rb") as f:
            while True:
                # 24x24px tile
                tile = f.read(0x120)
                if tile == b"":
                    break
                for i, mask in enumerate(masks):

                    # If it's not interleaved, the output is a 24/24 tile
                    if not self.interleaved:
                        pixel_data = [[0 for _ in range(24)] for _ in range(24)]
                    # Otherwise, the right half is interleaved with the left half
                    else:
                        pixel_data = [[0 for _ in range(12)] for _ in range(48)]

                    for byte_index, two_pixels in enumerate(tile):
                        masked = two_pixels & mask
                        for i, pixel in enumerate([masked & 0x0F, masked >> 4]):
                            if not self.interleaved:
                                x = (byte_index % 12) * 2 + i
                                y = math.floor(byte_index / 12)
                            else:
                                x = (byte_index % 12) * 2 + i
                                y = math.floor(byte_index / 12) * 2

                                if x >= 12:
                                    x = x - 12
                                    y += 1
                            pixel_data[y][x] = pixel

                    self.tiles.append(pixel_data)

    def dump(self, output_dir: str):
        """
        Output the full font sheet to a png file in <output_dir>
        """
        palette = [[255, 255, 255, 255], [0, 0, 0, 255], [0, 0, 0, 255], [0, 0, 0, 255]]
        # Arrange each tile out on a grid

        if not self.interleaved:
            tiles_wide = int(self.width / 24)
            tiles_high = int(self.height / 24)
        else:
            tiles_wide = int(self.width / 12)
            tiles_high = int(self.height / 48)

        temp_tile_pixels = [[0 for _ in range(tiles_wide)] for _ in range(tiles_high)]
        for i, tile in enumerate(self.tiles):
            y = math.floor(i / tiles_wide)
            x = i % tiles_wide
            temp_tile_pixels[y][x] = np.array(tile)

        # Use numpy to turn the grid into one massive pixel matrix
        tile_pixels = np.block(temp_tile_pixels)
        tile_pixels = tile_pixels.tolist()

        # Then write to file
        w = png.Writer(
            len(tile_pixels[0]),
            len(tile_pixels),
            palette=palette,
            bitdepth=4,
        )

        filename = f"{output_dir}/{self.title}.png"
        with open(filename, "wb") as image_f:
            w.write(image_f, tile_pixels)
    @staticmethod
    def print_tile(tile):
        """
        Debugging function to print out the contents of a tile
        """
        for row in tile:
            out = ""
            for item in row:
                if item == 0:
                    out += "□ "
                else:
                    out += "■ "
            print(out)

    def patch(self, png_filename: str):
        if self.interleaved:
            return self.patch_interleaved(png_filename)
        return self.patch_uninterleaved(png_filename)

    def patch_uninterleaved(self, png_filename: str):
        """
        Patch the full-width, uninterleaved font.
        """
        reader = png.Reader(filename=f"{png_filename}")
        width, height, rows, info = reader.read()
        if width != self.width or height != self.height:
            sys.exit(f"{png_filename} has incorrect dimensions")

        tiles_per_row = int(self.width / 24)
        tiles = []
        first = True
        row_tiles = [[[0 for _ in range(24)] for _ in range(24)] for _ in range(tiles_per_row)]
        for y, row in enumerate(rows):
            
            if y % 24 == 0 and not first:
                tiles += row_tiles
                row_tiles = [[[0 for _ in range(24)] for _ in range(24)] for _ in range(tiles_per_row)]

            for tile_i in range(tiles_per_row):
                pixels = row[tile_i*24:(tile_i+1)*24]
                if "palette" in info:
                    pixels = [0 if x == 0 else 1 for x in pixels]
                else:
                    pixels = [1 if r==g==b==0 else 0 for r,g,b,a in batched(pixels, 4)]
                    
                row_tiles[tile_i][y%24] = pixels

            if first:
                first = False

        if row_tiles !=  [[[0 for _ in range(24)] for _ in range(24)] for _ in range(tiles_per_row)]:
            tiles += row_tiles


        f = open(self.filename, "wb")
        for four_tiles in batched(tiles, 4):
            for y in range(24):
                for x in range(12):
                    # lol
                    bt = (
                        four_tiles[0][y][x * 2]
                        | four_tiles[0][y][(x * 2) + 1] << 4
                        | four_tiles[1][y][x * 2] << 1
                        | four_tiles[1][y][(x * 2) + 1] << 5
                        | four_tiles[2][y][x * 2] << 2
                        | four_tiles[2][y][(x * 2) + 1] << 6
                        | four_tiles[3][y][x * 2] << 3
                        | four_tiles[3][y][(x * 2) + 1] << 7
                    )
                    f.write(bt.to_bytes(1, "little"))


    def patch_interleaved(self, png_filename: str):
        """
        Patch the interleaved font
        """
        reader = png.Reader(filename=f"{png_filename}")
        width, height, rows, info = reader.read()
        if width != self.width or height != self.height:
            sys.exit(f"{png_filename} has incorrect dimensions")
        tiles = []
        pixel_data = []
        first = True
        for i, two_rows in enumerate(batched(rows, 2)):
            if i % 24 == 0 and not first:
                tiles.append(pixel_data)
                pixel_data = []

            # De-interleave each tile
            left = [x for x in two_rows[0]]
            if "palette" in info:
                left = [0 if x == 0 else 1 for x in left]
            else:
                if "alpha" in info and info["alpha"] == True:
                    left = [1 if r==g==b==0 else 0 for r,g,b,a in batched(left, 4)]
                else:
                    left = [1 if r==g==b==0 else 0 for r,g,b in batched(left, 3)]
            
            right = [x for x in two_rows[1]]
            if "palette" in info:
                right = [0 if x == 0 else 1 for x in right]
            else:
                if "alpha" in info and info["alpha"] == True:
                    right = [1 if r==g==b==0 else 0 for r,g,b,a in batched(right, 4)]
                else:
                    right = [1 if r==g==b==0 else 0 for r,g,b in batched(right, 3)]

            pixel_data.append(left + right)

            if first:
                first = False

        if pixel_data:
            tiles.append(pixel_data)

        f = open(self.filename, "wb")
        for four_tiles in batched(tiles, 4):
            for y in range(24):
                for x in range(12):
                    # lol
                    bt = (
                        four_tiles[0][y][x * 2]
                        | four_tiles[0][y][(x * 2) + 1] << 4
                        | four_tiles[1][y][x * 2] << 1
                        | four_tiles[1][y][(x * 2) + 1] << 5
                        | four_tiles[2][y][x * 2] << 2
                        | four_tiles[2][y][(x * 2) + 1] << 6
                        | four_tiles[3][y][x * 2] << 3
                        | four_tiles[3][y][(x * 2) + 1] << 7
                    )
                    f.write(bt.to_bytes(1, "little"))

    