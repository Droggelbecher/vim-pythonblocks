
import pynvim

import time
from threading import Lock
import sys
from pythonblocks import logging_ as logging
range_ = range
_executor_lock = Lock()
_nvim = None

logging.basicConfig(filename="/tmp/pythonblocks.log", level=logging.DEBUG)
_log = logging.getLogger(__name__)

@pynvim.plugin
class Plugin:
    def __init__(self, nvim):
        global _nvim
        self.nvim = nvim
        _nvim = nvim

    @pynvim.command('HelloWorld', nargs='*', range='')
    def helloworld(self, args, range):
        has_lock = _executor_lock.acquire(blocking=False)
        self.nvim.command(f"echomsg \"{sys.path}\"")

        if not has_lock:
            self.nvim.command("echomsg 'Theres another still running'")
            return

        try:
            pos = range[0]
            for i in range_(100):
                self.nvim.current.buffer[pos-1] = f"{id(self)} {pos} {i}"
                time.sleep(.1)

        finally:
            _executor_lock.release()

    @pynvim.command('ExecuteRange', nargs='*', range='')
    def execute_range(self, args, range):
        from . import cells

        has_lock = _executor_lock.acquire(blocking=False)

        if not has_lock:
            self.nvim.command("echomsg 'Theres another still running'")
            return

        try:
            cells.execute_cell(self.nvim.current.buffer.range(*range))

        finally:
            _executor_lock.release()

