meta:
  id: hgscript
  endian: le
seq:
  - id: num_routines
    type: u4
  - id: data_section_offset
    type: u4
  - id: routines
    type: routine
    repeat: expr
    repeat-expr: num_routines

types:
  routine:
    seq:
      - id: ofs_sequence
        type: u4
    instances:
      event_sequence:
        pos: ofs_sequence
        type: event_sequence
  
  event_sequence:
    seq:
      - id: events
        type: event
        repeat: until
        repeat-until: _.type_id == 0

  event:
    seq:
      - id: type_id
        type: b6le
      - id: raw_data
        type: b26le
    instances:
      body:
        type: 
          switch-on: type_id
          cases:
            0: end_sequence
            1: text
            2: newline
            3: unknown
            4: unknown
            5: screen_wipe
            6: sleep
            7: play_sound

  ###
  # EVENT TYPES
  ###

  unknown:
    instances:
      data:
        value: _parent.raw_data

  end_sequence:
    instances:
      data:
        value: _parent.raw_data

  text:
    instances:
      # Offset in words
      ofs_text_data:
        value: _parent.raw_data
      text_data:
        io: _root._io
        pos: (ofs_text_data << 2) + _root.data_section_offset
        type: text_data
  text_data:
    seq: 
      # For whatever reason, each string is prefixed with its width in pixels. It's
      # important to update this if you change the string as it's used to calculate
      # text positioning.
      - id: width_in_pixels
        type: u4
      - id: string
        type: str
        terminator: 0
        encoding: SJIS

  newline:
    instances:
      data:
        value: _parent.raw_data

  screen_wipe:
    instances:
      data:
        value: _parent.raw_data

  sleep:
    instances:
      duration_frames:
        value: _parent.raw_data

  play_sound:
    instances:
      # Offset in words.
      ofs_exst_ptr:
        value: _parent.raw_data
      
      # This corresponds to an an offset in 1.47.12.0029B700.bin, containing an EXST 
      # header for the sound effect. The SE data lives in stream.dat though I don't 
      # know how the pointer into that file is calculated.
      # To get to the offset in 1.47.12... you have to go through some weird calculations. 
      # For example if the value of ofs_exst_header is 0x241...
      # 0x241 << 4 = 0x2410
      # 0x2410 - 0x241 = 0x21cf
      # 0x21cf << 3 = 0x10e78
      # which is an offset in 1.47.12.0029B700.bin
      ofs_exst_header:
        type: u4
        pos: (ofs_exst_ptr << 2) + _root.data_section_offset