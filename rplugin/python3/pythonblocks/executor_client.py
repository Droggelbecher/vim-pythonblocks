
from .ipc import Reader, Writer
from pathlib import Path
import subprocess
from pythonblocks import logging_ as logging

_log = logging.getLogger(__name__)

class ExecutorClient:
    def __init__(self):
        self.python_path = "python3"
        self.script_path = Path(__file__).parent / "executor.py"

        self.process = subprocess.Popen(
            [self.python_path, self.script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0
        )
        _log.debug(f"Process: {self.script_path} {self.process}")
        self.reader = Reader(self.process.stdout.fileno())
        self.writer = Writer(self.process.stdin.fileno())

    def read(self):
        # TODO: check process alive / pipe open and react accordingly?
        return self.reader()

    def write(self, obj):
        # TODO: check process alive / pipe open and react accordingly?
        _log.debug(f"Writing process={self.process} writer={self.writer}")
        self.writer(obj)

