"""
Big ugly class for reading and writing from both 4bpp and 8bpp textures
"""

import math
import sys
from os import makedirs
from os.path import isdir

import numpy as np
import png

from .swizzling import get_maps_4bpp, get_maps_8bpp, swizzle, unswizzle

DEBUGGING = []


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

    def update_slices(self, pixels):
        """
        If the given pixel is a part of a defined slice, update that slice's pixel data
        """
        for slice in self.slices.values():
            whole_sheet = slice.get("whole_sheet", False)
            if whole_sheet:
                width = self.width
                height = self.height
                pos_x = 0
                pos_y = 0
            else:
                width = slice.get("width")
                height = slice.get("height")
                pos_x = slice["pos_x"]
                pos_y = slice["pos_y"]

            if "pixels" not in slice:
                if whole_sheet:
                    if self.bpp == 8:
                        slice["pixels"] = [
                            [0 for _ in range(self.width)] for _ in range(self.height)
                        ]
                    else:
                        slice["pixels"] = [
                            [0 for _ in range(self.width // 2)]
                            for _ in range((self.height * 4))
                        ]
                else:
                    slice["pixels"] = [[0 for _ in range(width)] for _ in range(height)]

            for item_y, row in enumerate(pixels[pos_y : pos_y + height]):
                for item_x, pixel in enumerate(row[pos_x : pos_x + width]):
                    slice["pixels"][item_y][item_x] = pixel

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
                self.height = int.from_bytes(f.read(4), byteorder="little") * 1
            elif self.bpp == 8:
                self.width = int.from_bytes(f.read(4), byteorder="little") * 2
                self.height = int.from_bytes(f.read(4), byteorder="little") * 2

            self.read_slice_palettes(f)

            f.seek(0x80)
            if self.bpp == 8:
                self.swizzle_map, self.deswizzle_map = get_maps_8bpp(
                    img_width=self.width, img_height=self.height
                )
                pixels = [[0 for _ in range(self.width)] for _ in range(self.height)]

                buf = f.read(self.width * self.height)
                for i, pixel in enumerate(buf):
                    y = i // (self.width * 2)
                    x = i % (self.width * 2)
                    real_x, real_y = unswizzle(x, y, self.deswizzle_map)

                    # In my testing these pixels are always 0 or palettes, so I
                    # guess I don't care. Not sure if it's an artifact of swizzling
                    # or a legit bug.
                    if (real_x >= self.width) or (real_y >= self.height):
                        continue
                    pixels[real_y][real_x] = pixel

                self.update_slices(pixels)
            elif self.bpp == 4:
                self.swizzle_map, self.deswizzle_map = get_maps_4bpp(
                    img_width=self.width, img_height=self.height
                )
                pixels = [
                    [0 for _ in range(self.width // 2)]
                    for _ in range((self.height * 4))
                ]
                buf = f.read(self.width * self.height)
                for i, two_pixels in enumerate(buf):
                    y = i // self.width
                    x = (i % self.width) * 2

                    for subpixel_index, pixel in enumerate(
                        [two_pixels >> 4, two_pixels & 0x0F]
                    ):
                        real_x, real_y = unswizzle(
                            x + subpixel_index, y, self.deswizzle_map
                        )

                        if (real_x >= self.width // 2) or (real_y >= self.height * 4):
                            continue
                        pixels[real_y][real_x] = pixel

                self.update_slices(pixels)

    def dump_slices(self, output_dir: str):
        """
        For each slice in self.slices, dump to pngs in <output_dir>
        """
        if not isdir(output_dir):
            makedirs(output_dir)

        for slice_name, slice in self.slices.items():
            filename = f"{output_dir}/{slice_name}.png"
            print(f"Dumping slice {slice_name}")
            pixel_data = slice["pixels"]

            pixel_data.reverse()

            w = png.Writer(
                len(pixel_data[0]),
                len(pixel_data),
                palette=slice["palette"],
                bitdepth=self.bpp,
            )
            with open(filename, "wb") as image_f:
                w.write(image_f, pixel_data)

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

        # Simply rotating the image in imagemagick seems to add a 17th color for 4bpp images. why??
        if (
            png_palette
            and self.bpp == 4
            and len(png_palette) == 17
            and png_palette[-1] in [(255, 255, 255), (255, 255, 255, 255)]
        ):
            png_palette = png_palette[:-1]

        if (
            png_palette
            and self.bpp == 4
            and len(inferred_palette) == 17
            and inferred_palette[-1] in [(255, 255, 255), (255, 255, 255, 255)]
        ):
            inferred_palette = inferred_palette[:-1]

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
        png_palette = [
            (0, 0, 0, 0) if p == (255, 255, 255, 0) else p for p in png_palette
        ]
        inferred_palette = [
            (0, 0, 0, 0) if p == (255, 255, 255, 0) else p for p in inferred_palette
        ]

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
