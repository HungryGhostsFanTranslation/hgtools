import json
import os
import functools


class InvalidDialogFileError(Exception):
    pass


""" Every string is prefixed by the total width of the
string in pixels. Because of that we need to know the 
in-game width of each of each character. """
with open("config/char_pixel_widths.json", "r") as f:
    CHAR_PIXEL_WIDTHS = json.load(f)


def calculate_text_width(s):
    """
    Given a text string, calculate the number of pixels it
    will take up in-game
    """
    length = 2
    # Each character is padded with one pixel on each side
    for c in s:
        width = CHAR_PIXEL_WIDTHS.get(c, None)
        if not width:
            raise ValueError("Received character with unknown width: %s. Update char_pixel_widths.json" % c)
        length += (width + 1)  # 1 pixel between each character
    return length


# Strings that shouldn't be translated.
DO_NOT_TRANSLATE = ["≪", "≫", "ＯＮ", "ＯＦＦ", "ＥＸＩＴ", "ＯＫ", "…", "〜", "■"]


class EventSequence:
    def __init__(self, fp, source_filename, event_data, id):
        self.events = []
        self.source_filename = source_filename
        self.first_event_type = None
        self.id = id

        prev_event_type = None
        while True:
            b = fp.read(4)
            if b == b"\x00\x00\x00\x00":
                break
            e = Event(b, sequence=self, event_index=len(self.events), prev_event_type=prev_event_type)
            if not self.first_event_type:
                self.first_event_type = e.type
            if e.type == 1:
                e.get_text(event_data)
            self.events.append(e)
            prev_event_type = e.type

    def serialize(self):
        if self.events == []:
            return None
        return functools.reduce(lambda seq, item: seq + item, [e.serialize() for e in self.events])


class Event:
    def __init__(self, b, sequence, event_index, prev_event_type):
        self.type, self.data_offset = self.parse_event_bytes(b)
        self.original_data_offset = self.data_offset
        self.sequence = sequence
        self.event_index = event_index  # Index of event in parent sequence
        self.prev_event_type = prev_event_type
        self.length = None
        self.text = None
        self.text_width = None

    @staticmethod
    def parse_event_bytes(b):
        event = int.from_bytes(b, "little")
        event_type = event & 0x3f
        data_offset = event >> 6 << 2
        return event_type, data_offset

    def serialize(self):
        return ((self.data_offset >> 2 << 6) + self.type).to_bytes(4, "little")

    def get_text(self, event_data):
        text_bytes = b""
        i = self.data_offset
        self.text_width = event_data[i:i + 4]
        i += 4
        while True:
            b = event_data[i:i + 1]
            if b == b"\x00":
                break
            text_bytes += b
            i += 1
        self.text = text_bytes.decode("shift-jis")
        # include text 4-byte header and null byte
        self.length = 4 + len(text_bytes) + 1


def unicode_chars(s):
    """ Return list of unicode chars in s"""
    out = ""
    for c in s:
        if not (0 <= ord(c) <= 127) and c not in out:
            out += c
    return out


def dump_event(event, script):
    body = {"source_filename": event.sequence.source_filename,
            "sequence_id": event.sequence.id,
            "event_id": event.event_index,
            "original_text": event.text,
            "translated_text": None,
            "prev_event_type": event.prev_event_type,
            "first_event_type": event.sequence.first_event_type}
    script.update(source_filename=event.sequence.source_filename, sequence_id=event.sequence.id,
                  event_index=event.event_index, body=body)


def translate_event(event, event_data, script):
    """ Given an Event and event data, translate event and
    return an updated event_data. """
    if event.type != 1:
        raise ValueError("Only can translate event type 1")
    pre = event_data[0:event.data_offset]
    post = event_data[event.data_offset + event.length:]

    if event.text in DO_NOT_TRANSLATE:
        return event_data

    translation = script.get(source_filename=event.sequence.source_filename, sequence_id=event.sequence.id,
                             event_id=event.event_index)
    if translation and translation.get("translated_text"):
        event.text = translation.get("translated_text")
        """
        If there are any unicode chars in the translation's text
        that don't have a defined width, this will throw an exception. 
        """
        new_width = calculate_text_width(event.text)

    else:
        new_width = int.from_bytes(event.text_width, "little")

    new_text = new_width.to_bytes(4, "little") + event.text.encode("shift-jis") + b"\x00"

    if len(new_text) < event.length:
        new_text += b"\x00" * (event.length - len(new_text))

    if ((len(new_text) - event.length) % 4) != 0:
        new_text += b"\x00" * (4 - ((len(new_text) - event.length) % 4))

    event.length = len(new_text)

    return pre + new_text + post


def fix_offsets(event_sequences, min_offset, delta):
    """ Fix any events whose 'data_offset' occurs after 'min_offset'.
    Delta is how many bytes the offsets need to change
    Could be more efficient but not necessary """
    for event_sequence in event_sequences:
        for event in event_sequence.events:
            if event.original_data_offset > min_offset:
                event.data_offset += delta


def process_sequences(event_sequences, event_data, script, translate=False):
    """
    Dump or translate a list of event sequences. Non-text events are left alone.
    """
    for event_sequence in event_sequences:
        for event in event_sequence.events:
            if event.type == 1:
                old_length = event.length
                if translate:
                    event_data = translate_event(event, event_data, script)
                    if event.length != old_length:
                        fix_offsets(event_sequences, event.original_data_offset + old_length, event.length - old_length)
                else:
                    dump_event(event, script)
    return event_sequences, event_data


def process_text(file_path, script, translate=False, has_object_header=False):
    """
    Given a HGScript file, unpack it, andd pull any Japanese text into <script>. If
    <translate> is True, it will replace text with translated strings from <script>.
    Finally, if <has_object_header> is True, skips past the object header.

    The object header is a list of references to objects in a level that maps the
    object to the text that shows when the MC inspects them.
    """

    data_offset = None
    with open(file_path, "rb") as f:
        if has_object_header:
            base_ptr = int.from_bytes(f.read(4), "little")
        else:
            base_ptr = 0

        f.seek(base_ptr)
        num_sequences = int.from_bytes(f.read(4), "little")
        data_offset = int.from_bytes(f.read(4), "little")
        f.seek(data_offset + base_ptr)
        event_data = f.read()
        sequences = []
        for sequence_index in range(0, num_sequences):
            f.seek(0x8 + (sequence_index * 4) + base_ptr)
            sequence_offset = int.from_bytes(f.read(4), "little")
            if sequence_offset == 0:
                # Sequence offset is an absolute pointer. Should never point to 0x0
                raise InvalidDialogFileError("This is not a valid dialog file")
            f.seek(sequence_offset + base_ptr)
            sequence = EventSequence(f, file_path, event_data, id=sequence_index)
            sequences.append(sequence)

    sequences, event_data = process_sequences(sequences, event_data, script, translate)

    if translate:
        with open(file_path, "r+b") as f:
            if has_object_header:
                base_ptr = int.from_bytes(f.read(4), "little")
            else:
                base_ptr = 0
            f.seek(base_ptr)
            num_sequences = int.from_bytes(f.read(4), "little")
            f.seek(4, 1)
            for sequence_index in range(0, num_sequences):
                f.seek(0x8 + (sequence_index * 4) + base_ptr)
                sequence_offset = int.from_bytes(f.read(4), "little")
                f.seek(sequence_offset + base_ptr)

                sequence_bytes = sequences[sequence_index].serialize()
                if sequence_bytes:
                    f.write(sequences[sequence_index].serialize())

            f.seek(data_offset + base_ptr)
            f.write(event_data)
