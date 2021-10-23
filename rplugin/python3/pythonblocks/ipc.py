
import os
import pickle
# from mylogging import debug

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
        try:
            if len(self._len_bytes) < 4:
                self._len_bytes += os.read(self._fd, 4 - len(self._len_bytes))
                if len(self._len_bytes) < 4:
                    return None

                self._len = sum([
                    x << (8*(3 - i))
                    for i, x in enumerate(self._len_bytes)
                ])

            if self._len is not None and len(self._data_bytes) < self._len:
                self._data_bytes += os.read(self._fd, self._len - len(self._data_bytes))
                if len(self._data_bytes) < self._len:
                    return None

                obj = pickle.loads(self._data_bytes)
                self._len_bytes = b''
                self._data_bytes = b''
                self._len = None
                return obj

        except BlockingIOError:
            pass
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
        # debug(f"writer writing {len_bytes} + {bytes_}")
        os.write(self._fd, len_bytes + bytes_)



