import io
import logging


logger = logging.getLogger(__name__)


class Seeker(object):
    """
    Seeker is a read-only, file-like object that can be used to wrap 
    non-seekable streams to provide lazy buffering and seeking functionality. 

    Notes:
        Unlike most io BaseBuffers subclasses, SeekableCache will only read() 
        from the underlying stream on demand. This ensures that it requests as 
        little data as possible.
    """

    def __init__(self, stream_fh, buffer=None):
        """
        Create a new Seeker instance.

        Args:
            stream_fh: A file-like object supporting `read` and `close` 
                methods, and the `closed` property.
            buffer: a readable/writeable/seekable buffer to be used to contain 
                data read from stream_fh. Defaults to None, which will cause 
                Seeker to use an `io.BytesIO` instance.
        """
        self._fh = stream_fh
        if self._fh.closed:
            raise ValueError("provided stream must already be open")
        
        self._buf_len = 0
        self._buf = buffer or io.BytesIO()
        
        self._log = logger.getChild("{classname}.{fp_id}".format(
            classname=self.__class__.__name__,
            fp_id=id(self._fh)))
        
        self._log.debug("creating SeekableCache with underlying fp: %r", 
            self._fh)

    def _extend(self, size=-1):
        """
        Attempt to extend the buffer by some number of bytes by reading from 
        the stream.

        Args:
            size (int): The number of bytes to attempt to read from the stream. 
                Defaults to -1, indicating that it should read until the stream 
                is closed (where `read()` returns an empty byte string).

        Returns:
            int: number of bytes extended
        """
        if self._fh.closed:
            return 0

        if size == -1:
            size = None

        # capture the initial position of the cursor and move it to EOF
        initial_pos = self._buf.tell()
        self._buf.seek(0, 2)

        written = 0
        while (size is None) or (written < size):
            block = self._fh.read(size)
            if block == b'': # eof
                break
            self._buf.write(block)
            written += len(block)
        self._buf.seek(initial_pos)

        self._buf_len += written
        
        self._log.debug("read %d bytes from underlying fp; extended buffer to "\
            "%d bytes", written, self._buf_len)

        return written

    def tell(self):
        """
        Determine the position of the cursor within the buffer.

        Returns:
            int: the absolute position of the cursor within the buffer
        """
        return self._buf.tell()

    def close(self):
        """
        Close the underlying stream and buffer simultaneously.
        """
        self._log.debug("closing underlying fp and buffer")
        self._fh.close()
        if hasattr(self._buf, 'close'):
            self._buf.close()

    def seekable(self):
        """
        Determine if the Seeker supports seeking.

        Returns:
            bool: always True for the Seeker; it's in the name ;)
        """
        return True

    def read(self, size=-1):
        self._log.debug("user requested %d bytes from buffer", size)
        cur_pos = self._buf.tell()

        # if size is 0, reader may be checking to see if "open in binary mode"
        if size == 0:
            return b''

        # if byte limit of -1 is provided, read everything
        elif size == -1:
            self._extend(size)
        
        # if the requested number of bytes exceeds the amount in the buffer
        elif ((cur_pos + size) > self._buf_len):
            bytes_needed = cur_pos + size - self._buf_len
            self._extend(bytes_needed)
            
        # read as needed...
        v = self._buf.read(size)

        self._log.debug("read %d bytes from buffer; cursor position is %d", 
            len(v), self._buf.tell())
        
        return v

    def seek(self, offset, whence=0):
        cur_pos = self._buf.tell()
        new_pos = cur_pos
        
        # the caller requests an absolute offset within the buffer
        if whence == 0:
            if offset > self._buf_len:
                delta_size = offset - self._buf_len
                self._extend(delta_size)
            new_pos = offset
        
        # the caller requests an offset within the buffer relative to the 
        # current cursor position
        elif whence == 1:
            if (cur_pos + offset) > self._buf_len:
                delta_size = (cur_pos + offset) - self._buf_len
                self._extend(delta_size)
            new_pos = cur_pos + offset
        
        # the caller requests an offset within the buffer relative to the end 
        # of the file
        elif whence == 2:
            self._extend()
            new_pos = self._buf_len + offset

        self._log.debug("seek %d (whence %d); cursor %d => %d", 
            offset, whence, cur_pos, new_pos)

        self._buf.seek(new_pos)