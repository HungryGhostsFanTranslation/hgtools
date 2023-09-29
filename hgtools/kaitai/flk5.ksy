meta:
  id: flk5
  endian: le
seq:
  - id: magic
    contents: 'FLK5'
  - id: num_files
    type: u4
  - id: len_total
    type: u4
  - id: unknown
    type: u4
  - id: files
    type: flk5_file(_index)
    repeat: expr
    repeat-expr: num_files
types:
  flk5_file:
    params:
      - id: i  # => receive `_index` as `i` here
        type: s4
    seq:
      - id: ofs_data
        type: b24le
      - id: file_type
        type: u1
    instances:
      data:
        io: _root._io
        pos: ofs_data
        # Read until the offset of the next file. If we're end the file, read til eof.
        size: 'i == (_parent.num_files-1) ? _parent.len_total - ofs_data : _parent.files[i+1].ofs_data - ofs_data' 