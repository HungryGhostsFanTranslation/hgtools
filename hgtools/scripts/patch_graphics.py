""" Extracts pack.dat """

import os
import sys
import shutil
import subprocess
import tempfile
from hglib.textures.known_textures import known_textures
from hglib.fonts.known_fonts import known_fonts
from hglib.textures.texture import Texture
from hglib.fonts.font import Font
from pathlib import Path
import click


@click.command()
@click.argument(
    "replacement_graphics_dir",
    type=click.Path(
        file_okay=False, dir_okay=True, readable=True, exists=False, writable=True
    ),
)
@click.argument(
    "path_to_unpacked",
    type=click.Path(file_okay=False, dir_okay=True, readable=True),
)
def patch_graphics(replacement_graphics_dir: str, path_to_unpacked: str):
    """
    Given a dir of graphics, quantize them, fliptate if need and then patch back into
    game files.
    """

    if not shutil.which("pngquant"):
        sys.exit(
            "pngquant not found. This is a requirement for this script. Install it first"
        )

    if not shutil.which("magick"):
        sys.exit(
            "ImageMagick not found. This is a requirement for this script. Install it first"
        )

    with tempfile.TemporaryDirectory() as tmpdir:

        # Quantize and fliptate graphics before patching them into game files
        for filename in os.listdir(replacement_graphics_dir):
            in_path = os.path.join(replacement_graphics_dir, filename)
            out_path = os.path.join(tmpdir, filename)
            temp_path = os.path.join(tmpdir, "temp.png")
            if "name_entry" in filename:
                subprocess.run(
                    [
                        "pngquant",
                        "16",
                        "--quality",
                        "1-90",
                        "--output",
                        temp_path,
                        in_path,
                    ]
                )
                shutil.copy(temp_path, out_path)
            elif "font" not in filename:
                subprocess.run(
                    [
                        "pngquant",
                        "256",
                        "--quality",
                        "1-90",
                        "--output",
                        temp_path,
                        in_path,
                    ]
                )
                subprocess.run(
                    ["magick", "-flop", "-rotate", "180", temp_path, out_path]
                )
            else:
                shutil.copyfile(in_path, out_path)
                Path(temp_path).touch()


            os.remove(temp_path)
        for file_path in known_textures.keys():
            full_path = os.path.join(path_to_unpacked, file_path)
            t = Texture(filename=full_path, slices=known_textures[file_path])

            for slice_name, slice in known_textures[file_path].items():

                png_path = os.path.join(tmpdir, f"{slice_name}.png")
                if not os.path.isfile(png_path):
                    continue
                print("Patching slice %s" % slice_name)
                t.patch_slice(slice_name, png_path, slice["pos_x"], slice["pos_y"])

        for file_path in known_fonts.keys():
            full_path = os.path.join(path_to_unpacked, file_path)

            title = known_fonts[file_path]["title"]
            width = known_fonts[file_path]["width"]
            height = known_fonts[file_path]["height"]
            interleaved = known_fonts[file_path]["interleaved"]

            png_path = os.path.join(tmpdir, f"{title}.png")
            font = Font(filename=full_path, title=title, width=width, height=height, interleaved=interleaved)
            font.patch(png_path)