import io

import pytest

from podstar import stream


def test_stream_seeker():
    fh = io.BytesIO(b'hello, I am the nicest seekable buffer')
    b = stream.Seeker(fh)

    assert b.tell() == 0, "empty cache's cursor should be at 0"
    
    assert b.read(5) == b'hello', "read from cursor 0 should work"
    assert b.tell() == 5, "after reading five bytes, cursor should be 5"
    assert b._buf_len == 5, "only five bytes should have been read from fh"

    assert b.read(6) == b', I am', "reading six more bytes should work"
    assert b.tell() == 11, "cursor should now be at position 11"
    assert b._buf_len == 11, "buffer should have grown to 11 bytes"

    assert b.read() == bytes(fh.getbuffer()[11:]), \
        "an unbound read should yield the remaining bytes in the buffer"
    assert b.tell() == len(fh.getvalue()), \
        "the cursor should be at the end of the buffer"

    b.seek(0)
    assert b.tell() == 0
    assert b.read() == bytes(fh.getbuffer()), \
        "reading all bytes from the buffer should be possible"

    b.seek(22)
    b.seek(-6, 1)
    assert b.tell() == 16, "seeking to relative offsets should work"
    assert b.read(6) == b'nicest', \
        "reading after seeking to a relative offset should work"

    b.seek(-6, 2)
    assert b.tell() == 32, \
        "seeking to an offset from the end of the file should work"
    assert b.read(6) == b'buffer', \
        "reading after seeking to an end-relative offset should work"

    b.close()
    assert (fh.closed and b._buf.closed), \
        "closing SeekableCache should close both underlying file handle and " \
        "buffer"