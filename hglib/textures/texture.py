"""
Big ugly class for reading and writing from both 4bpp and 8bpp textures
"""

from .swizzling import get_maps_8bpp, get_maps_4bpp, unswizzle, swizzle
import png
from .scramble_patterns import scramble_patterns
import numpy as np
import math
import sys


class Texture:
    def __init__(self, filename: str, slices: dict, bpp: int):
        self.filename = filename

        # A single texture is usually comprised of multiple smaller textures, each
        # with its own palette. I call these "slices"
        self.slices = slices
        self.bpp = bpp
        self.width = None
        self.height = None
        self.swizzle_map = None
        self.deswizzle_map = None
        self.read()

    def update_slices(self, real_x: int, real_y: int, pixel_value: int):
        """
        If the given pixel is a part of a defined slice, update that slice's pixel data
        """
        for slice in self.slices.values():
            width = slice.get("width")
            height = slice.get("height")
            pos_x = slice["pos_x"]
            pos_y = slice["pos_y"]
            whole_sheet = slice.get("whole_sheet", False)
            if not whole_sheet and not (
                real_x >= pos_x
                and real_x < (pos_x + width)
                and real_y >= pos_y
                and real_y < (pos_y + height)
            ):
                continue

            # If we're here, this pixel is part of a slice
            item_x = real_x - pos_x
            item_y = real_y - pos_y
            if not "pixels" in slice:
                if whole_sheet:
                    slice["pixels"] = [
                        [0 for _ in range(self.width)] for _ in range(self.height)
                    ]
                else:
                    slice["pixels"] = [[0 for _ in range(width)] for _ in range(height)]
            slice["pixels"][item_y][item_x] = pixel_value
            return

    @staticmethod
    def read_palette_8bpp(fp, offset):
        """Read a single 8bpp palette from <fp> starting at <offset>"""
        palette = [0] * 256
        for section_index in range(0, 8):
            fp.seek(offset + (0x800 * section_index))
            for i in range(0, 8):
                r, g, b, a = fp.read(4)
                a = (a * 2) - 1
                if a > 255:
                    a = 255
                elif a < 0:
                    a = 0
                palette[(section_index * 32) + i] = (r, g, b, a)
            for i in range(0, 8):
                r, g, b, a = fp.read(4)
                a = (a * 2) - 1
                if a > 255:
                    a = 255
                elif a < 0:
                    a = 0
                palette[(section_index * 32) + i + 16] = (r, g, b, a)
            fp.seek(offset + (0x800 * section_index) + 0x400)
            for i in range(0, 8):
                r, g, b, a = fp.read(4)
                a = (a * 2) - 1
                if a > 255:
                    a = 255
                elif a < 0:
                    a = 0
                palette[(section_index * 32) + i + 8] = (r, g, b, a)
            for i in range(0, 8):
                r, g, b, a = fp.read(4)
                a = (a * 2) - 1
                if a > 255:
                    a = 255
                elif a < 0:
                    a = 0
                palette[(section_index * 32) + i + 24] = (r, g, b, a)
        return palette


    def read_palette_4bpp(self, fp, offset):
        """Read a single 4bpp palette from <fp> starting at <offset>"""
        fp.seek(offset)
        palette = [0] * 16
        for i in range(0, 8):
            r, g, b, a = fp.read(4)
            a = (a * 2) - 1
            if a > 255:
                a = 255
            elif a < 0:
                a = 0
            palette[i] = (r, g, b, a)
        fp.seek(offset + self.width)
        for i in range(0, 8):
            r, g, b, a = fp.read(4)
            a = (a * 2) - 1
            if a > 255:
                a = 255
            elif a < 0:
                a = 0
            palette[i + 8] = (r, g, b, a)
        return palette

    @staticmethod
    def write_palette_8bpp(fp, offset, palette):
        """Replace the 8bpp palette at <offset> with <palette>"""
        fp.seek(offset)
        # Pad palette out to 256 entries if needed.
        palette += [(0, 0, 0, 0)] * (256 - len(palette))

        for section_index in range(0, 8):
            fp.seek(offset + (0x800 * section_index))
            for i in range(0, 8):
                r, g, b, a = palette[(section_index * 32) + i]
                a = math.ceil(a / 2)
                fp.write(r.to_bytes(length=1, byteorder="little"))
                fp.write(g.to_bytes(length=1, byteorder="little"))
                fp.write(b.to_bytes(length=1, byteorder="little"))
                fp.write(a.to_bytes(length=1, byteorder="little"))
            for i in range(0, 8):
                r, g, b, a = palette[(section_index * 32) + i + 16]
                a = math.ceil(a / 2)
                fp.write(r.to_bytes(length=1, byteorder="little"))
                fp.write(g.to_bytes(length=1, byteorder="little"))
                fp.write(b.to_bytes(length=1, byteorder="little"))
                fp.write(a.to_bytes(length=1, byteorder="little"))
            fp.seek(offset + (0x800 * section_index) + 0x400)
            for i in range(0, 8):
                r, g, b, a = palette[(section_index * 32) + i + 8]
                a = math.ceil(a / 2)
                fp.write(r.to_bytes(length=1, byteorder="little"))
                fp.write(g.to_bytes(length=1, byteorder="little"))
                fp.write(b.to_bytes(length=1, byteorder="little"))
                fp.write(a.to_bytes(length=1, byteorder="little"))
            for i in range(0, 8):
                r, g, b, a = palette[(section_index * 32) + i + 24]
                a = math.ceil(a / 2)
                fp.write(r.to_bytes(length=1, byteorder="little"))
                fp.write(g.to_bytes(length=1, byteorder="little"))
                fp.write(b.to_bytes(length=1, byteorder="little"))
                fp.write(a.to_bytes(length=1, byteorder="little"))


    def write_palette_4bpp(self, fp, offset, palette):
        """Replace the 4bpp palette at <offset> with <palette>"""
        fp.seek(offset)
        # Pad palette out to 16 entries if needed.
        palette += [(0, 0, 0, 0)] * (16 - len(palette))

        for i in range(0, 8):
            r, g, b, a = palette[i]
            a = math.ceil(a / 2)
            fp.write(r.to_bytes(length=1, byteorder="little"))
            fp.write(g.to_bytes(length=1, byteorder="little"))
            fp.write(b.to_bytes(length=1, byteorder="little"))
            fp.write(a.to_bytes(length=1, byteorder="little"))
        fp.seek(offset + self.width)
        for i in range(0, 8):
            r, g, b, a = palette[i + 8]
            a = math.ceil(a / 2)
            fp.write(r.to_bytes(length=1, byteorder="little"))
            fp.write(g.to_bytes(length=1, byteorder="little"))
            fp.write(b.to_bytes(length=1, byteorder="little"))
            fp.write(a.to_bytes(length=1, byteorder="little"))

    def is_palette(self, offset, palette_start):
        """
        Returns if the given offset is part of the palette at <palette_start>.
        Used to avoid overwriting palette data when patching pixel data.
        """
        if self.bpp == 4:
            return (palette_start <= offset <= (palette_start + 0x20)) or (
                palette_start + 0x400 <= offset <= (palette_start + 0x420)
            )
        elif self.bpp == 8:
            return (palette_start <= offset <= (palette_start + 0x40)) or (
                palette_start + 0x800 <= offset <= (palette_start + 0x840)
            )

    def read_slice_palettes(self, fp):
        """
        For all slices in self.slices, read their palette and store back in self.slices
        """
        for slice_name, slice in self.slices.items():
            # Allow for a hardcoded palette
            if "palette" in slice:
                continue
            if self.bpp == 8:
                self.slices[slice_name]["palette"] = self.read_palette_8bpp(
                    fp, slice["palette_offset"]
                )
            elif self.bpp == 4:
                self.slices[slice_name]["palette"] = self.read_palette_4bpp(
                    fp, slice["palette_offset"]
                )

    def read(self):
        """
        Read the binary texture file at <filename> and store various things in
        instance variables.
        1. Reads total width/height
        2. Populates swizzle/deswizzle maps
        3. Updates any defined slices
        """
        with open(self.filename, "rb") as f:
            self.header = f.read(0x80)

            f.seek(0x50)
            if self.bpp == 4:
                self.width = int.from_bytes(f.read(4), byteorder="little") * 4
            elif self.bpp == 8:
                self.width = int.from_bytes(f.read(4), byteorder="little") * 2
            self.height = int.from_bytes(f.read(4), byteorder="little") * 2

            self.read_slice_palettes(f)

            f.seek(0x80)
            if self.bpp == 8:
                self.swizzle_map, self.deswizzle_map = get_maps_8bpp(
                    img_width=self.width, img_height=self.height
                )
                for y in range(0, int(self.height / 2)):
                    for x in range(0, int(self.width * 2)):
                        pixel = int.from_bytes(f.read(1), "little")
                        real_x, real_y = unswizzle(x, y, self.deswizzle_map)
                        self.update_slices(real_x, real_y, pixel_value=pixel)
            elif self.bpp == 4:
                self.swizzle_map, self.deswizzle_map = get_maps_4bpp(
                    img_width=self.width, img_height=self.height
                )
                for y in range(0, int(self.height / 2)):
                    for x in range(0, int(self.width * 2), 2):
                        two_pixels = int.from_bytes(f.read(1), "little")
                        for i, pixel in enumerate([two_pixels >> 4, two_pixels & 0x0F]):
                            real_x, real_y = unswizzle(x + i, y, self.deswizzle_map)
                            self.update_slices(real_x, real_y, pixel_value=pixel)

    def dump_slices(self, output_dir: str):
        """
        For each slice in self.slices, dump to pngs in <output_dir>
        """
        for slice_name, slice in self.slices.items():
            filename = f"{output_dir}/{slice_name}.png"
            print(f"Dumping to {filename}")
            pixel_data = slice["pixels"]
            if slice["scrambled"]:
                width = slice["width"]
                height = slice["height"]
                scramble_pattern = scramble_patterns.get(f"{width}_{height}")
                if not scramble_pattern:
                    raise KeyError(f"No scramble pattern defined for {width}x{height}")
                unscrambled_pixels = self.unscramble(pixel_data, scramble_pattern)
                pixel_data = unscrambled_pixels

            w = png.Writer(
                len(pixel_data[0]),
                len(pixel_data),
                palette=slice["palette"],
                bitdepth=self.bpp,
            )
            with open(filename, "wb") as image_f:
                w.write(image_f, pixel_data)

    def dump_all(self, output_file_path: str):
        """
        Dump an entire texture with a hardcoded palette. Used to just get a rough
        idea what's in a texture file.
        """

    def get_tile(self, pixels, tile_x, tile_y):
        """
        Given coordinates of a single tile (tile_x, tile_y), grab the pixels of that
        tile.
        """
        tile_pixels = [[0 for _ in range(32)] for _ in range(16)]
        for y in range(tile_y * 16, (tile_y * 16) + 16):
            for x in range(tile_x * 32, (tile_x * 32) + 32):
                tile_pixels[y % 16][x % 32] = pixels[y][x]
        return np.array(tile_pixels)

    def unscramble(self, pixel_data, scramble_pattern):
        """
        Some textures are a scrambled mess of 32x16 tiles. This function will
        unscramble them using the patterns defined in unscramble_patterns.py
        """
        temp_tile_pixels = [
            [0 for _ in range(len(scramble_pattern[0]))]
            for _ in range(len(scramble_pattern))
        ]
        for y, row in enumerate(scramble_pattern):
            for x, tile_coords in enumerate(row):
                tile = self.get_tile(pixel_data, tile_coords[0], tile_coords[1])
                temp_tile_pixels[y][x] = tile
        tile_pixels = np.block(temp_tile_pixels)
        tile_pixels = tile_pixels.tolist()
        tile_pixels.reverse()
        return tile_pixels

    def rescramble(
        self, pixel_data, scramble_pattern, scrambled_width, scrambled_height
    ):
        """
        The inverse of unscramble()
        """
        pixel_data.reverse()
        tile_width = int(scrambled_width / 32)
        tile_height = int(scrambled_height / 16)
        temp_tile_pixels = [[0 for _ in range(tile_width)] for _ in range(tile_height)]
        for y, row in enumerate(scramble_pattern):
            for x, tile_coords in enumerate(row):
                tile = self.get_tile(pixel_data, x, y)
                temp_tile_pixels[tile_coords[1]][tile_coords[0]] = tile

        tile_pixels = np.block(temp_tile_pixels)
        tile_pixels = tile_pixels.tolist()

        return tile_pixels

    @staticmethod
    def infer_palette(png_filename: str):
        """
        Generate a palette from a PNG file, even if it doesn't use indexed-colors.
        """
        reader = png.Reader(filename=f"{png_filename}")
        width, height, rows, info = reader.read()

        inferred_palette = [(0, 0, 0, 0)]
        if "palette" in info:
            return info["palette"]
        for y, row in enumerate(rows):
            for x in range(0, width):
                pixel = (row[x * 4], row[x * 4 + 1], row[x * 4 + 2], row[x * 4 + 3])
                if pixel not in inferred_palette:
                    inferred_palette.append(pixel)
        return inferred_palette

    def patch_slice(self, slice_name, png_filename, pos_x, pos_y):
        """
        Given a replacement PNG, patch the pixel data and palette of a specific
        slice.
        """
        slice = self.slices[slice_name]
        reader = png.Reader(filename=f"{png_filename}")
        width, height, rows, info = reader.read()
        png_palette = info.get("palette")

        inferred_palette = self.infer_palette(png_filename)

        if png_palette and len(png_palette[0]) != 4:
            # pngquant eats the alpha channel if 100% of colors are max alpha
            # this will add the alpha channel back
            fixed_palette = []
            for color in png_palette:
                if len(color) == 3:
                    fixed_palette.append(color + (255,))
                else:
                    fixed_palette.append(color)
            png_palette = fixed_palette

            fixed_inferred_palette = []
            for color in inferred_palette:
                if len(color) == 3:
                    fixed_inferred_palette.append(color + (255,))
                else:
                    fixed_inferred_palette.append(color)
            inferred_palette = fixed_inferred_palette

        # Another palette fix
        png_palette = [(0,0,0,0) if p==(255,255,255,0) else p for p in png_palette]
        inferred_palette = [(0,0,0,0) if p==(255,255,255,0) else p for p in inferred_palette]
        

        if self.bpp == 4 and len(inferred_palette) > 16:
            sys.exit("Palette for %s is too big" % png_filename)

        f = open(self.filename, "r+b")
        if self.bpp == 8:
            self.write_palette_8bpp(
                f, offset=slice["palette_offset"], palette=inferred_palette
            )

            for y, row in enumerate(rows):
                for x in range(0, width):

                    # Translate a pixel from our replacement PNG to a value
                    # in <inferred_palette>.
                    if png_palette:
                        pixel = png_palette[row[x]]
                    elif len(row) == 4 * width:
                        pixel = (
                            row[x * 4],
                            row[x * 4 + 1],
                            row[x * 4 + 2],
                            row[x * 4 + 3],
                        )
                    else:
                        pixel = row[x]
                    if pixel == (255, 255, 255, 0):
                        pixel = (0, 0, 0, 0)

                    if pixel not in inferred_palette:
                        sys.exit("Found pixel not in palette: %s" % str(pixel))

                    pixel_value = inferred_palette.index(pixel)

                    # Find the proper swizzled address of the pixel and then write it
                    swizzled_x, swizzled_y = swizzle(
                        pos_x + x, pos_y + y, swizzle_map=self.swizzle_map
                    )
                    swizzled_address = (swizzled_y * self.width * 2) + swizzled_x
                    f.seek(0x80 + swizzled_address)
                    f.write(pixel_value.to_bytes(length=1, byteorder="little"))
        elif self.bpp == 4:
            self.write_palette_4bpp(
                f, offset=slice["palette_offset"], palette=inferred_palette
            )
            pixel_data = [[0 for _ in range(width)] for _ in range(height)]
            for y, row in enumerate(rows):
                for x in range(0, width):
                    # Translate a pixel from our replacement PNG to a value
                    # in <inferred_palette>.
                    if png_palette:
                        pixel = png_palette[row[x]]
                    elif len(row) == 4 * width:
                        pixel = (
                            row[x * 4],
                            row[x * 4 + 1],
                            row[x * 4 + 2],
                            row[x * 4 + 3],
                        )
                    else:
                        pixel = row[x]

                    if pixel == (255, 255, 255, 0):
                        pixel = (0, 0, 0, 0)

                    if pixel not in inferred_palette:
                        sys.exit("Found pixel not in palette: %s" % str(pixel))

                    pixel_value = inferred_palette.index(pixel)

                    # Store the value in pixel_data
                    pixel_data[y][x] = pixel_value

            # If this slice is scrambled, unscramble it before writing
            if slice["scrambled"]:
                width = slice["width"]
                height = slice["height"]
                scramble_pattern = scramble_patterns.get(f"{width}_{height}")
                if not scramble_pattern:
                    raise KeyError(f"No scramble pattern defined for {width}x{height}")
                rescrambled = self.rescramble(
                    pixel_data,
                    scramble_pattern,
                    width,
                    height,
                )
                pixel_data = rescrambled

            for y, row in enumerate(pixel_data):
                for x in range(0, len(row)):

                    # Find the proper swizzled address of the pixel and then write it
                    swizzled_x, swizzled_y = swizzle(
                        pos_x + x, pos_y + y, swizzle_map=self.swizzle_map
                    )

                    swizzled_address = (swizzled_y * self.width) + int(swizzled_x / 2)

                    # Skip any pixels that are palettes as we already wrote that earlier.
                    if self.is_palette(
                        0x80 + swizzled_address, slice["palette_offset"]
                    ):
                        continue

                    pixel_value = pixel_data[y][x]

                    f.seek(0x80 + swizzled_address)
                    current_byte = int.from_bytes(f.read(1), "little")
                    if swizzled_x % 2 == 0:
                        new_byte = (current_byte & 0xF) | pixel_value << 4
                    else:
                        new_byte = (current_byte & 0xF0) | pixel_value

                    f.seek(0x80 + swizzled_address)
                    f.write(new_byte.to_bytes(length=1, byteorder="little"))
