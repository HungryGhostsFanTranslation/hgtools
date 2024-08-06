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

bpp_by_slice_name = {}
for texture in known_textures.values():
    for slice_name, contents in texture.items():
        bpp_by_slice_name[slice_name] = contents["bpp"]

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
            slice_name = filename.split(".png")[0] 

            in_path = os.path.join(replacement_graphics_dir, filename)
            out_path = os.path.join(tmpdir, filename)
            temp_path = os.path.join(tmpdir, "temp.png")
            if "note_bg" in filename or "inv_" in filename:
                shutil.copyfile(in_path, out_path)
                Path(temp_path).touch()
            elif slice_name not in bpp_by_slice_name:
                # Fonts mostly
                shutil.copyfile(in_path, out_path)
                Path(temp_path).touch()
            elif bpp_by_slice_name[slice_name] == 4:
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
            elif bpp_by_slice_name[slice_name] == 8:
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
                    ["magick", temp_path, "-flop", "-rotate", "180", out_path]
                )


            os.remove(temp_path)
        for file_path in known_textures.keys():
            full_path = os.path.join(path_to_unpacked, file_path)
            slices = known_textures[file_path]
            # Assume the entire file is the same bpp
            # This may bite me later
            bpp = list(slices.values())[0]["bpp"]

            t = Texture(filename=full_path, slices=slices, bpp=bpp)

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
            print(f"Patching font {title}")
            font = Font(
                filename=full_path,
                title=title,
                width=width,
                height=height,
                interleaved=interleaved,
            )
            font.patch(png_path)
