# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Flk5(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.magic = self._io.read_bytes(4)
        if not self.magic == b"\x46\x4C\x4B\x35":
            raise kaitaistruct.ValidationNotEqualError(b"\x46\x4C\x4B\x35", self.magic, self._io, u"/seq/0")
        self.num_files = self._io.read_u4le()
        self.len_total = self._io.read_u4le()
        self.unknown = self._io.read_u4le()
        self.files = []
        for i in range(self.num_files):
            self.files.append(Flk5.Flk5File(i, self._io, self, self._root))


    class Flk5File(KaitaiStruct):
        def __init__(self, i, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self.i = i
            self._read()

        def _read(self):
            self.ofs_data = self._io.read_bits_int_le(24)
            self._io.align_to_byte()
            self.file_type = self._io.read_u1()

        @property
        def data(self):
            if hasattr(self, '_m_data'):
                return self._m_data

            io = self._root._io
            _pos = io.pos()
            io.seek(self.ofs_data)
            self._m_data = io.read_bytes(((self._parent.len_total - self.ofs_data) if self.i == (self._parent.num_files - 1) else (self._parent.files[(self.i + 1)].ofs_data - self.ofs_data)))
            io.seek(_pos)
            return getattr(self, '_m_data', None)



