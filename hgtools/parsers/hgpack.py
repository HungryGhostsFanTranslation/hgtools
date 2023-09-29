# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Hgpack(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.directories = []
        for i in range(272):
            self.directories.append(Hgpack.Directory(self._io, self, self._root))


    class Directory(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.directory_id = self._io.read_u4le()
            self.num_files = self._io.read_u4le()
            self.first_flk5_reverse_offset = self._io.read_u4le()
            self.first_file_ofs = self._io.read_u4le()
            self.first_flk5_ofs = self._io.read_u4le()
            self.total_flk5_size = self._io.read_u4le()

        @property
        def num_flk5s(self):
            if hasattr(self, '_m_num_flk5s'):
                return self._m_num_flk5s

            _pos = self._io.pos()
            self._io.seek(32)
            self._m_num_flk5s = self._io.read_u4le()
            self._io.seek(_pos)
            return getattr(self, '_m_num_flk5s', None)

        @property
        def files(self):
            if hasattr(self, '_m_files'):
                return self._m_files

            _pos = self._io.pos()
            self._io.seek(64)
            self._m_files = []
            for i in range(self.num_files):
                self._m_files.append(Hgpack.File(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_files', None)


    class File(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ofs_data = self._io.read_u4le()
            self.len_data = self._io.read_u4le()
            self.unknown = self._io.read_u4le()
            self.unused = self._io.read_u4le()

        @property
        def data(self):
            if hasattr(self, '_m_data'):
                return self._m_data

            io = self._root._io
            _pos = io.pos()
            io.seek(self.ofs_data)
            self._m_data = io.read_bytes(self.len_data)
            io.seek(_pos)
            return getattr(self, '_m_data', None)



