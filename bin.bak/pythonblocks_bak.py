import datetime
import pickle
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict
from .ipc import Reader, Writer


# def send_object(object_, filelike):
    # bytes_ = pickle.dumps(object_)
    # len_ = len(bytes_)
    # len_bytes = bytes([(len_ >> (8 * (3 - i))) & 0xFF for i in range(4)])
    # filelike.write(len_bytes + bytes_)
    # filelike.flush()


# def receive_object(filelike):
    # filelike.flush()
    # len_bytes = filelike.read(4)
    # len_ = sum([x << (8 * (3 - i)) for i, x in enumerate(len_bytes)])
    # data_bytes = filelike.read(len_)
    # return pickle.loads(data_bytes)


class SubprocessInterpreter:
    """
    Manages the lifecycle of the executor subprocess
    """
    def __init__(self, python_path="python3"):
        self.script_path = Path(__file__).parent.absolute() / "executor.py"
        self.python_path = python_path
        self.subprocess = subprocess.Popen(
            [self.python_path, self.script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.writer = Writer(self.subprocess.stdin.fileno)
        self.reader = Reader(self.subprocess.stdout.fileno)

    def exit(self):
        if self.subprocess:
            self.writer({"type": "exit"})

    def restart(self, python_path=None):
        """
        Restart the executor subprocess,
        optionally with a different python executable.
        """
        if python_path is not None:
            self.python_path = python_path

        self.exit()

        self.subprocess = subprocess.Popen(
            [self.python_path, self.script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def execute(self, cell, magics=[]):
        """
        Execute the contens of the given cell.
        `cell` will be modified to contain the execution results and additional information.

        Args:
            cell (Cell): Cell te execute.
            magics: Tokens of magics line to apply.
        Return:
            Passed cell.
        """
        retcode = self.subprocess.poll()
        if retcode is not None:
            print(self.subprocess.stderr.read(), file=sys.stderr)

        self.writer(
            {"type": "exec", "code": cell.code, "magics": magics}
        )

        # TODO: How to keep reading here without blocking, should vimscript poll
        # or should we spawn a thread?
        d = self.reader()
        for k, v in d.items():
            setattr(cell, k, v)
        return cell

    def wait_result(self, cell, range_, insertion_point):
        d = self.reader()
        while d is None:
            if getconfig("expand_marker") and insertion_point >= 0:
                range_[insertion_point] = format_waiting(cell)


class Cell:
    code = ""
    expressions = ()
    return_value = None
    values: Dict[str, Any] = {}
    started = None
    dt = None
    stdout = ""
    stderr = ""

    def __init__(self):
        self.started = time.time()


_interpreter = None


def init():
    global _interpreter
    _interpreter = SubprocessInterpreter(python_path=getconfig("python_path"))


def getconfig(c, type_=str, default=None):
    import vim  # type: ignore
    return vim.vars.get("pythonblocks#" + c, default)


def restart(python_path=None):
    _interpreter.restart(python_path)

def exit():
    _interpreter.exit()


def run_range():
    import vim  # type: ignore

    p = getconfig("marker_prefix")
    m_cell = p + getconfig("marker_cell")
    m_value = p + getconfig("marker_value")
    m_stdout = p + getconfig("marker_stdout")
    m_stderr = p + getconfig("marker_stderr")
    m_magic = p + getconfig("marker_magic")

    range_ = vim.current.range


    code = ""
    magics = []
    for line in range_[:]:
        l = line.strip()
        if l.startswith(m_magic):
            rest = l[len(m_magic) :]
            magics.extend(x.strip() for x in rest.split())

        if not l.startswith(p):
            code += line + "\n"

    cell = Cell()
    cell.code = code

    _interpreter.execute(cell, magics=magics)

    # Find insertion position: before the first cell boundary that is not in the first line
    # default to end
    insertion_point = -1
    for i, line in enumerate(range_[1:]):
        if line.strip().startswith(m_cell):
            insertion_point = i + 1
            break

    _interpreter.write_result(cell, range_, insertion_point)

    if getconfig("expand_marker") and insertion_point >= 0:
        range_[insertion_point] = format_marker(cell)

    l = []

    if getconfig("insert_stdout"):
        for out in cell.stdout.splitlines():
            l.append(f"{m_stdout} {out}")

    if getconfig("insert_stderr"):
        for err in cell.stderr.splitlines():
            l.append(f"{m_stderr} {err}")

    # if not _suppress_none_return or cell.return_value is not None:
    c = getconfig("insert_return")
    if ((c == "not_none") and (cell.return_value is not None)) or c == True:
        if cell.return_value is None:
            l.append(f"{m_value} None")
        else:
            for line in cell.return_value.splitlines():
                l.append(f"{m_value} {line}")

    for k, v in tuple(cell.values.items()):
        lines = v.splitlines()
        l.append(f"{m_value} {k} = {lines[0]}")
        for line in lines[1:]:
            l.append(f"{m_value} ...{' ' * len(k)}{line}")

    if insertion_point >= 0:
        range_.append(l, insertion_point)
    else:
        range_.append(l)

def test_executor():
    py2 = SubprocessInterpreter('python3')
    cell = Cell()
    cell.code = '''
import sys
print("Hello, World!")
sys.version
'''
    py2.execute(cell)
    print(cell.return_value)
    print(cell.stdout)
    print(cell.stderr)


