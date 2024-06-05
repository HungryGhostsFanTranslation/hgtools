import os
import yaml
import sys
from io import BytesIO
from typing import BinaryIO

from hglib.padding import padding


class BadFLK5Exception(Exception):
    pass


class FLK5File:
    """
    One file from an FLK5 archive. Just a stream of bytes and a file type.
    """

    def __init__(self, contents: bytes, type: int):
        self.contents = contents
        self.type = type

    @property
    def size(self):
        return len(self.contents)

    @classmethod
    def from_file(cls, path):
        if not os.path.exists(path):
            sys.exit(f"Failed to build FLK5File from file. {path} does not exist")
        type = int(os.path.basename(path).split(".")[-1])
        contents = b""
        with open(path, "rb") as f:
            contents = f.read()
        return cls(contents=contents, type=type)


class FLK5Archive:
    """
    An FLK5 archive (called this because of its 4-byte file signature) is effectively
    a nested directory in the Hungry Ghost pack.dat "filesystem". It expands to another
    set of files.
    """

    def __init__(self, files: list[FLK5File], unkn_pack_flags: int):
        self.files: list[FLK5File] = files
        # An unknown 4-byte set of flags that comes from pack.dat
        self.unkn_pack_flags = unkn_pack_flags

    @property
    def num_files(self):
        return len(self.files)

    @property
    def header_size(self):
        """Size of just the header and file-pointer section"""
        hs = 0x10 + (0x4 * self.num_files)
        # Word-aligned
        if (hs % 0x10) != 0:
            hs += 0x10 - (hs % 0x10)
        return hs

    @property
    def size(self):
        """Size of entire archive"""
        total_size = self.header_size
        for file in self.files:
            total_size += file.size
        return total_size

    def to_bytes(self) -> BytesIO:
        """Serialize to bytes"""
        out = BytesIO()
        out.write(b"FLK5")
        out.write(self.num_files.to_bytes(4, byteorder="little"))
        out.write(self.size.to_bytes(4, byteorder="little"))
        # Padding
        out.write(b"\x00\x00\x00\x00")

        # Skip the file pointer section for now and do it after writing the file data
        out.seek(self.header_size)
        # List of tuples, each container a file's pointer and its type
        files_info = []
        for file in self.files:
            files_info.append((out.tell(), file.type))
            out.write(file.contents)

        # Now finish up the file pointer section
        out.seek(0x10)
        for file_ptr, file_type in files_info:
            out.write(file_ptr.to_bytes(3, byteorder="little"))
            out.write(file_type.to_bytes(1, byteorder="little"))

        if out.tell() > self.header_size:
            sys.exit(
                "Overran expected header size when writing file pointer section! Crashing"
            )

        return out

    def to_dir(self, path):
        if not os.path.isdir(path):
            sys.exit(f"Could not unpack FLK5 because dir {path} does not exist")
        for i, file in enumerate(self.files):
            filename = f"{i}.{file.type}"
            file_path = os.path.join(path, filename)
            with open(file_path, "wb") as fp:
                fp.write(file.contents)

    @classmethod
    def from_packed(cls, fp: BytesIO, unkn_pack_flags: int):
        if fp.read(4) != b"FLK5":
            raise BadFLK5Exception("Provided file is not a FLK5 file")
        num_files = int.from_bytes(fp.read(4), "little")
        _size = int.from_bytes(fp.read(4), "little")
        file_info = []

        # This is literally always 0
        zero = int.from_bytes(fp.read(4), "little")
        if zero != 0:
            sys.exit("FLK5 header padding actually had a value in it?")

        for _ in range(num_files):
            # First, build a list of section pointers + types
            # This is necessary because as far as I can tell length has to be inferred
            # First 3 bytes are pointer to start of data
            data_pointer = int.from_bytes(fp.read(3), "little")
            # 4th byte is a file type
            file_type = int.from_bytes(fp.read(1), "little")
            file_info.append((data_pointer, file_type))

        # Now build each file into an FLK5File
        files = []
        for file_index in range(num_files):
            data_pointer, file_type = file_info[file_index]
            fp.seek(data_pointer)
            if file_index == (num_files - 1):
                # Last item. Read to end of file
                data = fp.read()
            else:
                # Infer the file length by looking at the start of next
                file_length = file_info[file_index + 1][0] - data_pointer
                data = fp.read(file_length)
            files.append(FLK5File(contents=data, type=file_type))
        return FLK5Archive(files=files, unkn_pack_flags=unkn_pack_flags)

    @classmethod
    def from_dir(cls, path: str):
        """
        Given a path to an unpacked FLK5 archive, build it into an FLK5Archive
        """
        if not os.path.exists(path):
            sys.exit(f"Failed to build FLK5Archive from file. {path} does not exist")
        filename = os.path.basename(path)
        unkn_pack_flags = int(filename.split(".")[-1])
        files = []
        for filename in sorted(os.listdir(path), key=lambda fn: int(fn.split(".")[0])):
            file_path = os.path.join(path, filename)
            files.append(FLK5File.from_file(file_path))
        return cls(files=files, unkn_pack_flags=unkn_pack_flags)


class HGPackFile:
    """
    A file from inside an HGPackDir.
    """

    def __init__(self, contents: bytes, unkn_pack_flags: int):
        self.contents = contents
        self.unkn_pack_flags = unkn_pack_flags

    def to_bytes(self) -> BytesIO:
        return BytesIO(self.contents)

    @property
    def size(self):
        return len(self.contents)

    @classmethod
    def from_file(cls, path):
        if not os.path.exists(path):
            sys.exit(f"Failed to build HGPackFile from file. {path} does not exist")
        filename = os.path.basename(path)

        unkn_pack_flags = int(filename.split(".")[-1])
        contents = b""
        with open(path, "rb") as f:
            contents = f.read()
        return cls(contents=contents, unkn_pack_flags=unkn_pack_flags)


class HGPackDir:
    def __init__(
        self,
        first_file_ofs: int,
        unknown_a: int,
        unknown_b: int,
        unknown_c: int,
        unknown_d: int,
        unknown_e: int,
        unknown_f: int,
        files_or_dirs: list[HGPackFile | FLK5Archive] = None,
        first_file_ofs_corresponding_item: int | None = None,
        unknown_b_corresponding_item: int | None = None,
    ):
        if not files_or_dirs:
            self.files_or_dirs = []
        else:
            self.files_or_dirs = files_or_dirs

        """
        It's not really fair to call all of these unknown, because I spent some time 
        reversing them. However I've but have been unable to come to solid conclusons
        about how they work. <unknown_a> for example appears to be an index of the
        first FLK5 file, where all FLK5 files are stored in one contiguous block.
        However, directory 189 is a counterexample of this where file 23 is a FLK5 file
        despite being separated from the other FLK5s. As long as I don't change the 
        order of files, I can just leave this as-is.

        <unknown_b> almost always is where the data from this directory ends. In other 
        words, it's a pointer to where the next directory's data begins. Not always the
        case though, but thankfully appears unused.

        <unknown_c> appears to be correlated to the size of just the FLK5 files, but
        I found plenty of counterexamples and couldn't find any code using it.

        <unknown_f> often correlates to the number of FLK5s, but then other times
        doesn't. 

        Since I can't figure out what these do, I just keep track of them. 
        """

        self.unknown_a = unknown_a
        self.unknown_b = unknown_b
        self.unknown_c = unknown_c
        self.unknown_d = unknown_d
        self.unknown_e = unknown_e
        self.unknown_f = unknown_f

        self.first_file_ofs_corresponding_item = first_file_ofs_corresponding_item
        self.unknown_b_corresponding_item = unknown_b_corresponding_item

        # In most situations this will be automatically be generated when this
        # is serialized. However HGPackDirs with 0 items still have it set.
        # There's a chance I can just set to whatever, but just in case I
        # keep track of it.
        self.first_file_ofs = first_file_ofs

    def to_dir(self, path):
        if not os.path.isdir(path):
            sys.exit(f"Could not unpack pack.dat because dir {path} does not exist")

        # Write meta.yml
        meta_path = os.path.join(path, "meta.yml")

        metadata = {
            "first_file_ofs": self.first_file_ofs,
            "unknown_a": self.unknown_a,
            "unknown_b": self.unknown_b,
            "unknown_c": self.unknown_c,
            "unknown_d": self.unknown_d,
            "unknown_e": self.unknown_e,
            "unknown_f": self.unknown_f,
            "first_file_ofs_corresponding_item": self.first_file_ofs_corresponding_item,
            "unknown_b_corresponding_item": self.unknown_b_corresponding_item
        }

        with open(meta_path, "w") as fp:
            yaml.dump(metadata, fp)

        # Now write files to disk and expand FLK5Archives
        for i, item in enumerate(self.files_or_dirs):
            filename = f"{i}.{item.unkn_pack_flags}"
            file_path = os.path.join(path, filename)
            if isinstance(item, HGPackFile):
                with open(file_path, "wb") as fp:
                    fp.write(item.contents)
            elif isinstance(item, FLK5Archive):
                os.makedirs(file_path)
                item.to_dir(file_path)

    @property
    def num_files(self):
        return len(self.files_or_dirs)

    @classmethod
    def from_dir(cls, path):
        """
        Given a path to one unpacked PACK.dat directory, build it into a HGPackDir
        """

        if not os.path.exists(path):
            sys.exit(f"Failed to build HGPackDir from file. {path} does not exist")

        try:
            with open(os.path.join(path, "meta.yml"), "r") as yaml_f:
                metadata = yaml.safe_load(yaml_f)
        except FileNotFoundError:
            sys.exit(
                "Tried to process an unpacked pack.dat dir but there was no meta.yml file"
            )

        path_contents = os.listdir(path)
        if "meta.yml" in path_contents:
            path_contents.remove("meta.yml")
        if ".DS_Store" in path_contents:
            path_contents.remove(".DS_Store")
        path_contents = sorted(path_contents, key=lambda fn: int(fn.split(".")[0]))

        files_or_dirs = []
        for file_or_dir in path_contents:
            full_path = os.path.join(os.path.join(path, file_or_dir))
            if os.path.isdir(full_path):
                files_or_dirs.append(FLK5Archive.from_dir(full_path))
            else:
                files_or_dirs.append(HGPackFile.from_file(full_path))

        return cls(
            files_or_dirs=files_or_dirs,
            first_file_ofs=metadata["first_file_ofs"],
            unknown_a=metadata["unknown_a"],
            unknown_b=metadata["unknown_b"],
            unknown_c=metadata["unknown_c"],
            unknown_d=metadata["unknown_d"],
            unknown_e=metadata["unknown_e"],
            unknown_f=metadata["unknown_f"],
            first_file_ofs_corresponding_item=metadata["first_file_ofs_corresponding_item"],
            unknown_b_corresponding_item=metadata["unknown_b_corresponding_item"]
        )


class HGPack:
    def __init__(self, directories: list[HGPackDir]):
        self.directories: list[HGPackDir] = directories

    def to_dir(self, path: str):
        if not os.path.isdir(path):
            sys.exit(f"Could not unpack pack.dat because dir {path} does not exist")
        for i, dir in enumerate(self.directories):
            filename = f"{i}"
            file_path = os.path.join(path, filename)
            os.makedirs(file_path)
            dir.to_dir(file_path)

    def to_packed(self, file_path: str):
        fp = open(file_path, "wb")

        # Data section first
        data_start = len(self.directories) * 0x800
        fp.seek(data_start)
        # Indexed by HGPackDir, then item in that dir
        data_pointers = [[] for i in range(len(self.directories))]
        data_lens = [[] for i in range(len(self.directories))]

        for dir_index, dir in enumerate(self.directories):
            # An item is either a HGPackFile or an FLK5Archive
            for item_index, item in enumerate(dir.files_or_dirs):
                data_pointers[dir_index].append(fp.tell())
                length = fp.write(item.to_bytes().getbuffer())
                data_lens[dir_index].append(length)

                # Get proper byte-alignment, and add padding if needed.
                pad_amount = padding.get(f"{dir_index}.{item_index}", 0x80)

                if fp.tell() % pad_amount != 0:
                    fp.write(b"\x00" * (pad_amount - (fp.tell() % pad_amount)))

            # Extra padding at end of each directory
            if fp.tell() % 0x800 != 0:
                fp.write(b"\x00" * (0x800 - (fp.tell() % 0x800)))

        # Now write the non-data portions at the beginning of the file
        for dir_index, dir in enumerate(self.directories):
            fp.seek(0x800 * dir_index)
            fp.write(dir_index.to_bytes(4, byteorder="little"))
            fp.write(dir.num_files.to_bytes(4, byteorder="little"))
            fp.write(dir.unknown_a.to_bytes(4, byteorder="little"))

            # If these two items were pointers to known locations, adjust them
            # as needed.
            if dir.first_file_ofs_corresponding_item is not None:
                dir_i, file_i = dir.first_file_ofs_corresponding_item.split("/")
                dir_i = int(dir_i)
                file_i = int(file_i)
                dir.first_file_ofs = data_pointers[dir_i][file_i]

            if dir.unknown_b_corresponding_item is not None:
                dir_i, file_i = dir.unknown_b_corresponding_item.split("/")
                dir_i = int(dir_i)
                file_i = int(file_i)
                dir.unknown_b = data_pointers[dir_i][file_i]

                # I'm pretty sure unknown_c is the size of all of the files+dirs AFTER
                # the file unknown_b points to. This bit calculates that.
                # If unknown_b points outside this dir though don't bother
                if dir_i == dir_index:
                    unknown_c_size = (data_pointers[dir_i][-1] + dir.files_or_dirs[-1].size - dir.unknown_b)
                    dir.unknown_c = unknown_c_size  + (0x80 - (unknown_c_size % 80)) + 0x80

            fp.write(dir.first_file_ofs.to_bytes(4, byteorder="little"))
            fp.write(dir.unknown_b.to_bytes(4, byteorder="little"))
            fp.write(dir.unknown_c.to_bytes(4, byteorder="little"))
            fp.write(dir.unknown_d.to_bytes(4, byteorder="little"))
            fp.write(dir.unknown_e.to_bytes(4, byteorder="little"))
            fp.write(dir.unknown_f.to_bytes(4, byteorder="little"))

            # The rest is just padding.
            fp.write(b"\x00" * 0x1C)

            for item_index, item in enumerate(dir.files_or_dirs):
                data_ptr = data_pointers[dir_index][item_index]
                fp.write(data_ptr.to_bytes(4, byteorder="little"))
                data_len = data_lens[dir_index][item_index]
                fp.write(data_len.to_bytes(4, byteorder="little"))
                fp.write(item.unkn_pack_flags.to_bytes(4, byteorder="little"))
                fp.seek(4, 1)  # Word alignment

        fp.close()

    @classmethod
    def from_dir(cls, path):
        if not os.path.exists(path):
            sys.exit(f"Failed to build HGPack from dir. {path} does not exist")

        path_contents = os.listdir(path)
        if ".DS_Store" in path_contents:
            path_contents.remove(".DS_Store")
        if len(path_contents) != 273:
            sys.exit(
                f"Found an incorrect number of dirs in {path}. No support for adding/removing dirs"
            )
        path_contents = sorted(path_contents, key=lambda fn: int(fn))

        dirs = []
        for dir in path_contents:
            dir_path = os.path.join(path, dir)
            dirs.append(HGPackDir.from_dir(dir_path))

        return cls(directories=dirs)

    @classmethod
    def from_packed(cls, fp: BinaryIO):
        # Read in directory headers first
        dirs = []
        orig_ptrs_by_dir = []
        for dir_index in range(273):
            orig_ptrs = []
            fp.seek(dir_index * 0x800)
            # This should just equal dir_index
            dir_index_packed = int.from_bytes(fp.read(0x04), byteorder="little")
            if dir_index_packed != dir_index:
                print("expected: %d" % dir_index)
                print("got: %d" % dir_index_packed)
                sys.exit("Dir index doesn't match. Corrupted pack.dat?")

            # Number of files or subdirs (FLK5 archives)
            num_items = int.from_bytes(fp.read(0x04), byteorder="little")
            unknown_a = int.from_bytes(fp.read(0x04), byteorder="little")
            first_file_ofs = int.from_bytes(fp.read(0x04), byteorder="little")
            unknown_b = int.from_bytes(fp.read(0x04), byteorder="little")
            unknown_c = int.from_bytes(fp.read(0x04), byteorder="little")
            unknown_d = int.from_bytes(fp.read(0x04), byteorder="little")
            unknown_e = int.from_bytes(fp.read(0x04), byteorder="little")
            unknown_f = int.from_bytes(fp.read(0x04), byteorder="little")

            # These two values are important, but I've been unable to figure out
            # exactly how they work. My solution for now is to keep track of which
            # file/dir they point to in meta.yml and then change them to the new
            # pointer for that file/dir when it's time to write back to pack.dat.
            first_file_ofs_corresponding_item = None
            unknown_b_corresponding_item = None

            # The rest is just padding.
            fp.seek(0x1C, 1)

            item_info = []
            # Next is a list of files/subdirs, their size and an unknown property.
            for _item_index in range(num_items):
                item_ptr = int.from_bytes(fp.read(0x04), byteorder="little")

                item_size = int.from_bytes(fp.read(0x04), byteorder="little")
                unkn_pack_flags = int.from_bytes(fp.read(0x04), byteorder="little")
                fp.seek(0x4, 1)  # Word alignment
                item_info.append((item_ptr, item_size, unkn_pack_flags))

            files_or_dirs = []
            # Now process the data section
            for item_ptr, item_size, unkn_pack_flags in item_info:
                orig_ptrs.append(item_ptr)
                fp.seek(item_ptr)
                contents = fp.read(item_size)
                if contents[0:4] == b"FLK5":
                    files_or_dirs.append(
                        FLK5Archive.from_packed(
                            BytesIO(contents), unkn_pack_flags=unkn_pack_flags
                        )
                    )
                else:
                    files_or_dirs.append(
                        HGPackFile(contents=contents, unkn_pack_flags=unkn_pack_flags)
                    )
            dirs.append(
                HGPackDir(
                    files_or_dirs=files_or_dirs,
                    first_file_ofs=first_file_ofs,
                    unknown_a=unknown_a,
                    unknown_b=unknown_b,
                    unknown_c=unknown_c,
                    unknown_d=unknown_d,
                    unknown_e=unknown_e,
                    unknown_f=unknown_f,
                    first_file_ofs_corresponding_item=None,
                    unknown_b_corresponding_item=None
                )
            )
            orig_ptrs_by_dir.append(orig_ptrs)

        # Since unknown_b and first_file_ofs can point to files OUTSIDE of their own
        # HGPackDir, I have to do this hack where I figure out what their new value is
        # at the very end.
        for dir in dirs:
            first_file_ofs = dir.first_file_ofs
            unknown_b = dir.unknown_b

            for dir_index, dir_ptrs in enumerate(orig_ptrs_by_dir):
                for file_index, ptr in enumerate(dir_ptrs):
                    if ptr == first_file_ofs:
                        dir.first_file_ofs_corresponding_item = f"{dir_index}/{file_index}"
                    if ptr == unknown_b:
                        dir.unknown_b_corresponding_item = f"{dir_index}/{file_index}"
            
        return cls(directories=dirs)
