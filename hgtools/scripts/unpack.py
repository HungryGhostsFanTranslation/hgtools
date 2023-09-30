""" Extracts pack.dat """
import os
import shutil
from hgtools.parsers.hgpack import Hgpack
from hgtools.parsers.flk5 import Flk5
import click
import yaml

"""
      - id: first_flk5_reverse_offset 
        type: u4
      - id: first_file_ofs
        type: u4
      - id: first_flk5_ofs
        type: u4
      - id: total_flk5_size
        type: u4
      # These are properly an offset/file count for another file type.
      - id: unknown_a
        type: u4
      - id: unknown_b
        type: u4
      - id: num_flk5s
        type: u4
    instances:
"""


def write_metadata(directory: Hgpack.Directory, current_dir: str):
    body = {
        "id": directory.id,
        "num_files": directory.num_files,
        "first_flk5_reverse_index": directory.first_flk5_reverse_index,
        "first_file_ofs": directory.first_file_ofs,
        "total_flk5_size": directory.total_flk5_size,
        "unknown_a": directory.unknown_a,
        "unknown_b": directory.unknown_b,
        "num_flk5s": directory.num_flk5s,
    }
    with open(os.path.join(current_dir, "meta.yml"), "w") as f:
        yaml.dump(body, f)


@click.command()
@click.argument(
    "path_to_pack_dat",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.argument(
    "output_dir",
    type=click.Path(
        file_okay=False, dir_okay=True, readable=True, exists=False, writable=True
    ),
)
@click.option(
    "force",
    "-f",
    is_flag=True,
    default=False,
    help="Don't ask before deleting files inside OUTPUT_DIR",
)
def unpack(path_to_pack_dat: str, output_dir: str, force: bool):
    """
    Unpacks all files from the pack.dat pack file. Additionally unpacks any of the
    files which are FLK5 files.
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if os.listdir(output_dir) and not force:
        response = input(
            f"Warning! {output_dir} is not empty. This script will delete any files/directories inside. Continue? [y/n]: "
        )
        if response.lower() != "y":
            print("Exiting")
            return

    # Empty out output dir
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

    pack = Hgpack.from_file(path_to_pack_dat)
    for directory in pack.directories:
        id = directory.id
        current_dir = os.path.join(output_dir, str(id))
        os.makedirs(current_dir)

        write_metadata(directory, current_dir)

        for i,file in enumerate(directory.files):
            magic = file.data[0:4]
            if magic == b"FLK5":
                flk5 = Flk5.from_bytes(file.data)
                flk5_dir = os.path.join(current_dir, f"{i}.{flk5.unknown}") # Add the unknown var to the directory so I can restore it 
                os.makedirs(flk5_dir)
                for j, flk5_file in enumerate(flk5.files):
                    filename = f"{j}.{flk5_file.file_type}"
                    with open(os.path.join(flk5_dir, filename), "wb") as f:
                        f.write(flk5_file.data)
            else:
                with open(os.path.join(current_dir, f"{i}.{file.unknown}.bin"), "wb") as f:
                    f.write(file.data)
