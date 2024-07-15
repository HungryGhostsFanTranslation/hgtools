"""
Hungry Ghosts contains a simple scripting language for displaying text that is used for
most text in the game. It has events for newlines, coloring text, and even playing
sounds. This module contains classes to unpack the bytecode into an XML file and then
to build those XML files back into the binary files.
"""

import functools
import os
import sys
from base64 import b64decode, b64encode
from enum import Enum
from itertools import pairwise
from typing import BinaryIO

from defusedxml.ElementTree import ParseError, parse

from hglib.char_pixel_widths import char_pixel_widths
from hglib.orig_hgscript_filesizes import orig_hgscript_filesizes


def is_ascii(c):
    c_as_int = ord(c)
    return c_as_int >= 0 and c_as_int <= 0x7f

def calculate_text_width(s):
    """
    Given a text string, calculate the number of pixels it
    will take up in-game. Takes into account character width
    as well as kerning.
    """
    length = 0
    for c, next_c in pairwise(s):
        length += get_pair_width(c, next_c)

    # Pairwise will drop the last character, so we calculate that separately
    # Use " " as the right char just as a means to get the kerning-less width.
    length += get_pair_width(s[-1], " ")

    return length

def get_pair_width(c, next_c):
    """
    Given a character and the character to its right, figure out it's full width
    including any kerning.
    """
    if not is_ascii(c):
        width = 24
    else:
        if not is_ascii(next_c):
            width = char_pixel_widths[c][" "]
        else:
            width = char_pixel_widths[c][next_c]
    return width

class EventType(Enum):
    unknown_0 = 0
    text = 1
    newline = 2
    change_color = 3
    placeholder = 4
    screen_wipe = 5
    sleep = 6
    play_sound = 7
    unknown_11 = 11
    unknown_tag = 12
    button = 14


class InvalidHGScriptException(Exception):
    pass


class Event:
    """
    An Event is represented on-disk as 4 bytes and contains a 6-bit event type as well
    as 26 bits of extra data. Depending on the event type those 26 bits may be
    interpreted literally or may be a pointer into the parent HGScriptCollection's data
    section.
    """

    def __init__(self, type: EventType, data: int, extra_data: bytes):
        self.type = type
        self.data = data
        self.extra_data = extra_data

        # Used only for text events
        self.text = None
        self.text_width = None

        # Used only for play sound events
        self.sound_data = None

        # Used only for unknown_tag events
        self.unknown_tag_data = None

        # Everything else should only be run when we're initializing from packed
        if not extra_data:
            return

        if type == EventType.text:
            self.text, self.text_width = self.get_text_and_width()

        if type == EventType.play_sound:
            self.sound_data = self.get_sound_data()

        if type == EventType.unknown_tag:
            self.unknown_tag_data = self.get_unknown_tag_data()

    def to_xml(self):
        """
        Represent an event as XML
        """
        if self.type in (EventType.screen_wipe, EventType.newline):
            # Add an extra newline for screen wipes and newlines for readability
            return f"<{self.type.name}/>\n"
        if self.type == EventType.text:
            return f'<text width="{self.text_width}">{self.text}</text>'
        if self.type == EventType.play_sound:
            return (
                f'<play_sound>{b64encode(self.sound_data).decode("utf-8")}</play_sound>'
            )
        if self.type == EventType.unknown_tag:
            return f"<unknown_tag>{self.unknown_tag_data}</unknown_tag>"

        if self.type == EventType.change_color:
            attr_name = "color_id"
        elif self.type == EventType.sleep:
            attr_name = "frames"
        else:
            attr_name = "data"

        if self.data == 0:
            return f"<{self.type.name}/>"
        else:
            return f'<{self.type.name} {attr_name}="{self.data}"/>'

    def get_text_and_width(self):
        """
        Follow a text event's pointer and pull out the text data.
        """
        text_bytes = b""
        i = self.data << 2
        text_width = int.from_bytes(self.extra_data[i : i + 4], "little")
        i += 4
        while True:
            b = self.extra_data[i : i + 1]
            if b == b"\x00":
                break
            text_bytes += b
            i += 1
        text = text_bytes.decode("shift-jis")
        return text, text_width

    def get_sound_data(self):
        """
        Follow a play sound event's pointer and pull out the sound metadata.
        """
        i = self.data << 2
        sound_data = b""
        while True:
            b = self.extra_data[i : i + 4]
            sound_data += b
            if b == b"\xff\xff\xff\xff":
                break
            i += 4
        return sound_data

    def get_unknown_tag_data(self):
        """
        Grab the data section for a unknown_tag event. I don't know exactly what this
        represents.
        """
        i = self.data << 2
        unknown_tag_data = int.from_bytes(self.extra_data[i : i + 8], "little")
        return unknown_tag_data

    def to_bytes(self) -> bytes:
        return ((self.data << 6) + self.type.value).to_bytes(4, "little")

    @classmethod
    def from_bytes(cls, bts: bytes, extra_data: bytes):
        event = int.from_bytes(bts, "little")
        event_type = EventType(event & 0x3F)
        data = event >> 6  # If this is a pointer, it will later shift left by 2
        return cls(type=event_type, data=data, extra_data=extra_data)


class HGScript:
    """
    A script contains a list of Events which are evaluated sequentially until script
    completion.
    """

    def __init__(self, events: list[Event], extra_data: bytes):
        self.events = events
        self.extra_data = extra_data

    def to_xml(self):
        out = "<hgscript>\n"
        for event in self.events:
            out += event.to_xml()
        out += "\n</hgscript>"

        return out

    def to_bytes(self) -> bytes:
        if len(self.events) == 0:
            return b""
        return functools.reduce(
            lambda seq, item: seq + item, [e.to_bytes() for e in self.events]
        )

    @classmethod
    def from_io(cls, fp: BinaryIO, extra_data: bytes):
        """Read a sequence of events from a BinaryIO stream"""
        events = []
        while True:
            bts = fp.read(4)
            if bts == b"\x00\x00\x00\x00":
                break

            event = Event.from_bytes(bts, extra_data=extra_data)
            events.append(event)
        return cls(events=events, extra_data=extra_data)

    @classmethod
    def from_file(cls, path, extra_data: bytes):
        """
        Parse a dumped .xml file back into an HGScript. Also pulls out text/sound data
        and adds it into <extra_data>
        """
        if not os.path.exists(path):
            sys.exit(f"Failed to build HGScript from file. {path} does not exist")
        try:
            tree = parse(path)
        except ParseError:
            sys.exit(f"Failed to parse XML file at {path}.")

        root = tree.getroot()
        events = []
        for event in root:
            if event.tag in ("text", "play_sound", "unknown_tag"):
                # Word-alignment
                if len(extra_data) % 4 != 0:
                    extra_data += b"\x00" * (4 - (len(extra_data) % 4))
                data_ptr = len(extra_data)

                event_data = data_ptr >> 2

                if event.tag == "text":
                    # This characters have been "sacrificed" (see below)
                    # As such they cannot appear in the game script
                    if "$" in event.text or "%" in event.text:
                        raise ValueError(f"Disallowed character found in event text: {event.text}")

                    # Replace all ellipsis with "$" which we have patched in the font
                    # to be an ellipsis
                    event.text = event.text.replace("…", "$").replace("...", "$")
                    # Similarly, we swapped "%" for emdash
                    event.text = event.text.replace("—", "%").replace("–", "%")
                    encoded_text = event.text.encode("shift-jis")

                    width = calculate_text_width(event.text)

                    extra_data += width.to_bytes(4, "little") + encoded_text + b"\x00"
                elif event.tag == "play_sound":
                    sound_data = b64decode(event.text)
                    extra_data += sound_data
                elif event.tag == "unknown_tag":
                    unknown_tag_data = int(event.text).to_bytes(8, "little")
                    extra_data += unknown_tag_data

            else:
                if event.attrib:
                    event_data = int(list(event.attrib.values())[0])
                else:
                    event_data = 0

            e = Event(type=EventType[event.tag], data=event_data, extra_data=b"")
            events.append(e)

        return cls(events=events, extra_data=extra_data)


class HGScriptCollection:
    """
    A single file typically contains a number of distinct scripts. It additionally
    contains a data section which is used by various Event types.
    """

    def __init__(
        self, scripts: list[HGScript], extra_data: bytes, object_header: bytes
    ):
        self.scripts = scripts
        self.object_header = object_header
        self.extra_data = extra_data

    def to_dir(self, path):
        """
        Dump all contained scripts as XML files in a directory
        """
        if not os.path.isdir(path):
            sys.exit(f"Tried to dump HGScriptCollection but {path} does not exist")
        for i, script in enumerate(self.scripts):
            file_path = os.path.join(path, f"{i}.xml")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(script.to_xml())

        if self.object_header:
            file_path = os.path.join(path, f"object_header.bin")
            with open(file_path, "wb") as object_header_fp:
                object_header_fp.write(self.object_header)

    def to_file(self, path):
        """
        Pack into a binary file
        """
        fp = open(path, "wb")

        if self.object_header:
            fp.write(self.object_header)
            base_ptr = fp.tell()
        else:
            base_ptr = 0

        num_scripts = len(self.scripts)
        fp.write(num_scripts.to_bytes(4, "little"))

        # Here is where the pointer to the extra_data section. Save the location and
        # come back later to write it.
        extra_data_ptr_location = fp.tell()
        fp.seek(4, 1)

        # Now seek past the script pointer section
        fp.seek(4 * num_scripts, 1)

        # Write script contents
        script_ptrs = []

        for script in self.scripts:
            script_ptrs.append(fp.tell() - base_ptr)
            fp.write(script.to_bytes())
            fp.write(b"\x00\x00\x00\x00")

        # Extra data starts on the nearest 16th byte
        if fp.tell() % 16 != 0:
            fp.write(b"\x00" * (16 - (fp.tell() % 16)))

        # Write extra data
        extra_data_ptr = fp.tell() - base_ptr
        fp.write(self.extra_data)

        # Final file is padded out to 0x10?
        # I think this is actually only needed when the dialog file is NOT in a flk5
        # This hacky check is an attempt to check for if this is inside a FLK5
        if path.count("/") != 2:
            if fp.tell() % 16 != 0:
                fp.write(b"\x00" * (16 - (fp.tell() % 16)))

        # Magic padding voodoo magic
        orig_filesize = orig_hgscript_filesizes[path]
        current_size = fp.tell()
        if current_size < orig_filesize:
            fp.write(b"\x00" * (orig_filesize - current_size))

        # Now finish up by writing the pointers skipped earlier
        fp.seek(extra_data_ptr_location)
        fp.write(extra_data_ptr.to_bytes(4, "little"))

        for script_ptr in script_ptrs:
            fp.write(script_ptr.to_bytes(4, "little"))

        fp.close()

    @classmethod
    def from_file(cls, filename: str, has_object_header: bool = False):
        """
        Parse a binary HGScriptCollection file
        """
        with open(filename, "rb") as f:
            # If there is an object header, the first 4 bytes tell us where the actual
            # file starts.
            if has_object_header:
                base_ptr = int.from_bytes(f.read(4), "little")
                f.seek(0)
            else:
                base_ptr = 0
            object_header = f.read(base_ptr)

            num_scripts = int.from_bytes(f.read(4), "little")
            data_offset = int.from_bytes(f.read(4), "little")

            f.seek(data_offset + base_ptr)

            extra_data = f.read()

            scripts = []
            for script_index in range(0, num_scripts):
                f.seek(0x8 + (script_index * 4) + base_ptr)
                script_offset = int.from_bytes(f.read(4), "little")
                if script_offset == 0:
                    # Sequence offset is an absolute pointer. Should never point to 0x0
                    raise InvalidHGScriptException(
                        f"{filename} is not a valid dialog file"
                    )

                f.seek(script_offset + base_ptr)
                script = HGScript.from_io(fp=f, extra_data=extra_data)
                scripts.append(script)
        return cls(scripts=scripts, extra_data=extra_data, object_header=object_header)

    @classmethod
    def from_dir(cls, path: str):
        """
        Given a path to a dumped HGScriptCollection, build it into an HGScriptCollection
        """
        if not os.path.exists(path):
            sys.exit(
                f"Failed to build HGScriptCollection from dir. {path} does not exist"
            )
        filename = os.path.basename(path)

        path_contents = os.listdir(path)
        if "object_header.bin" in path_contents:
            path_contents.remove("object_header.bin")
            file_path = os.path.join(path, "object_header.bin")
            with open(file_path, "rb") as f:
                object_header = f.read()
        else:
            object_header = b""

        scripts = []
        extra_data = b""
        for filename in sorted(path_contents, key=lambda fn: int(fn.split(".")[0])):
            file_path = os.path.join(path, filename)

            script = HGScript.from_file(path=file_path, extra_data=extra_data)
            scripts.append(script)
            extra_data = script.extra_data
        return cls(scripts=scripts, extra_data=extra_data, object_header=object_header)
