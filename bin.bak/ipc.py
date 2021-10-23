
import os
import pickle
from mylogging import debug

class Reader:
    """
    """
    def __init__(self, fd):
        self._fd = fd
        os.set_blocking(self._fd, False)
        self._len_bytes = b''
        self._len = None
        self._data_bytes = b''

    def __call__(self):
        # debug(f"reader: len={self._len} len(len)={len(self._len_bytes)} len(data)={len(self._data_bytes)}")

        try:
            if len(self._len_bytes) < 4:
                # debug(f"reader: reading len ({self._len_bytes})")
                self._len_bytes += os.read(self._fd, 4 - len(self._len_bytes))
                if len(self._len_bytes) < 4:
                    # debug("reader return")
                    return None

                self._len = sum([
                    x << (8*(3 - i))
                    for i, x in enumerate(self._len_bytes)
                ])
                # debug(f"reader: done reading len: {self._len}")

            if self._len is not None and len(self._data_bytes) < self._len:
                # debug(f"reader: len: {self._len} len(data)={len(self._data_bytes)} data={self._data_bytes}")

                self._data_bytes += os.read(self._fd, self._len - len(self._data_bytes))
                if len(self._data_bytes) < self._len:
                    # debug("reader return")
                    return None

                obj = pickle.loads(self._data_bytes)
                # debug(f"reader: done reading data {obj}")
                self._len_bytes = b''
                self._data_bytes = b''
                self._len = None
                # debug("reader return")
                return obj

        except BlockingIOError:
            pass

        # debug("reader return")
        return None

class Writer:
    def __init__(self, fd):
        self._fd = fd

    def __call__(self, obj):
        bytes_ = pickle.dumps(obj)
        len_ = len(bytes_)
        len_bytes = bytes([
            (len_ >> (8*(3 - i))) & 0xff
            for i in range(4)
        ])
        debug(f"writer writing {len_bytes} + {bytes_}")
        os.write(self._fd, len_bytes + bytes_)
        # os.fsync(self._fd)



