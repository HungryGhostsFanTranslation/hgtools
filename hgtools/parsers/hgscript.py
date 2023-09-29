# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Hgscript(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.num_routines = self._io.read_u4le()
        self.data_section_offset = self._io.read_u4le()
        self.routines = []
        for i in range(self.num_routines):
            self.routines.append(Hgscript.Routine(self._io, self, self._root))


    class Routine(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ofs_sequence = self._io.read_u4le()

        @property
        def event_sequence(self):
            if hasattr(self, '_m_event_sequence'):
                return self._m_event_sequence

            _pos = self._io.pos()
            self._io.seek(self.ofs_sequence)
            self._m_event_sequence = Hgscript.EventSequence(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, '_m_event_sequence', None)


    class Event(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.type_id = self._io.read_bits_int_le(6)
            self.raw_data = self._io.read_bits_int_le(26)

        @property
        def body(self):
            if hasattr(self, '_m_body'):
                return self._m_body

            _on = self.type_id
            if _on == 0:
                self._m_body = Hgscript.EndSequence(self._io, self, self._root)
            elif _on == 4:
                self._m_body = Hgscript.Unknown(self._io, self, self._root)
            elif _on == 6:
                self._m_body = Hgscript.Sleep(self._io, self, self._root)
            elif _on == 7:
                self._m_body = Hgscript.PlaySound(self._io, self, self._root)
            elif _on == 1:
                self._m_body = Hgscript.Text(self._io, self, self._root)
            elif _on == 3:
                self._m_body = Hgscript.Unknown(self._io, self, self._root)
            elif _on == 5:
                self._m_body = Hgscript.ScreenWipe(self._io, self, self._root)
            elif _on == 2:
                self._m_body = Hgscript.Newline(self._io, self, self._root)
            return getattr(self, '_m_body', None)


    class ScreenWipe(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass

        @property
        def data(self):
            if hasattr(self, '_m_data'):
                return self._m_data

            self._m_data = self._parent.raw_data
            return getattr(self, '_m_data', None)


    class EventSequence(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.events = []
            i = 0
            while True:
                _ = Hgscript.Event(self._io, self, self._root)
                self.events.append(_)
                if _.type_id == 0:
                    break
                i += 1


    class Sleep(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass

        @property
        def duration_frames(self):
            if hasattr(self, '_m_duration_frames'):
                return self._m_duration_frames

            self._m_duration_frames = self._parent.raw_data
            return getattr(self, '_m_duration_frames', None)


    class Unknown(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass

        @property
        def data(self):
            if hasattr(self, '_m_data'):
                return self._m_data

            self._m_data = self._parent.raw_data
            return getattr(self, '_m_data', None)


    class Text(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass

        @property
        def ofs_text_data(self):
            if hasattr(self, '_m_ofs_text_data'):
                return self._m_ofs_text_data

            self._m_ofs_text_data = self._parent.raw_data
            return getattr(self, '_m_ofs_text_data', None)

        @property
        def text_data(self):
            if hasattr(self, '_m_text_data'):
                return self._m_text_data

            io = self._root._io
            _pos = io.pos()
            io.seek(((self.ofs_text_data << 2) + self._root.data_section_offset))
            self._m_text_data = Hgscript.TextData(io, self, self._root)
            io.seek(_pos)
            return getattr(self, '_m_text_data', None)


    class TextData(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.width_in_pixels = self._io.read_u4le()
            self.string = (self._io.read_bytes_term(0, False, True, True)).decode(u"SJIS")


    class Newline(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass

        @property
        def data(self):
            if hasattr(self, '_m_data'):
                return self._m_data

            self._m_data = self._parent.raw_data
            return getattr(self, '_m_data', None)


    class EndSequence(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass

        @property
        def data(self):
            if hasattr(self, '_m_data'):
                return self._m_data

            self._m_data = self._parent.raw_data
            return getattr(self, '_m_data', None)


    class PlaySound(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass

        @property
        def ofs_exst_ptr(self):
            if hasattr(self, '_m_ofs_exst_ptr'):
                return self._m_ofs_exst_ptr

            self._m_ofs_exst_ptr = self._parent.raw_data
            return getattr(self, '_m_ofs_exst_ptr', None)

        @property
        def ofs_exst_header(self):
            if hasattr(self, '_m_ofs_exst_header'):
                return self._m_ofs_exst_header

            _pos = self._io.pos()
            self._io.seek(((self.ofs_exst_ptr << 2) + self._root.data_section_offset))
            self._m_ofs_exst_header = self._io.read_u4le()
            self._io.seek(_pos)
            return getattr(self, '_m_ofs_exst_header', None)



