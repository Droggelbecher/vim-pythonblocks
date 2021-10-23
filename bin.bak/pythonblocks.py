
import threading
import subprocess
from pathlib import Path
import time
import sys
import datetime
import pickle
from typing import Any, Dict
from ipc import Reader, Writer
import re
from mylogging import debug

# logging.basicConfig(filename='/tmp/pythonblocks.log', level=logging.DEBUG)
# log = logging.getLogger(__name__)

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
            bufsize=0
        )
        self.writer = Writer(self.subprocess.stdin.fileno())
        self.reader = Reader(self.subprocess.stdout.fileno())
        debug(f"subprocess={self.subprocess} stdin={self.subprocess.stdin} fileno={self.subprocess.stdin.fileno()}")

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

        debug(f"EXEC {cell.code}")
        self.writer(
            {"type": "exec", "code": cell.code, "magics": magics}
        )

    def wait_result(self, cell, range_, insertion_point):
        d = self.reader()
        while d is None:
            # debug(f"pyblocks waiting {getconfig('expand_marker')} {insertion_point}")
            if getconfig("expand_marker") and insertion_point >= 0:
                range_[insertion_point] = cell.format_waiting()
                time.sleep(0.1)
            d = self.reader()

        for k, v in d.items():
            setattr(cell, k, v)

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

    def format_waiting(cell):
        m_cell = getconfig("marker_prefix") + getconfig("marker_cell")
        template = getconfig("waiting_template")

        value = cell.return_value
        oneline_value = value.splitlines()[0] if isinstance(value, str) else value

        return (
            m_cell
            + " "
            + template.format(
                **{
                    "dt": time.time() - cell.started,
                    "time": datetime.datetime.now(),
                }
            )
        )


    def format_marker(cell):
        m_cell = getconfig("marker_prefix") + getconfig("marker_cell")
        template = getconfig("marker_template")

        value = cell.return_value
        oneline_value = value.splitlines()[0] if isinstance(value, str) else value

        return (
            m_cell
            + " "
            + template.format(
                **{
                    "dt": cell.dt,
                    "value": oneline_value,
                    "value_unless_none": oneline_value if oneline_value is not None else "",
                    "time": datetime.datetime.now(),
                }
            )
        )



_interpreter = None

def init():
    global _interpreter
    debug("Pythonblocks initialized")

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
    # t = threading.Thread(target=run_range_async)
    # t.start()
    p = getconfig("marker_prefix")
    m_cell = p + getconfig("marker_cell")

    # Find insertion position: before the first cell boundary that is not in the first line
    # default to end
    insertion_point = -1
    range_ = vim.current.range
    for i, line in enumerate(range_[1:]):
        debug(f"LINE {i} {line}")
        if line.strip().startswith(m_cell):
            insertion_point = i + 1
            break
    vim.async_call(run_range_async, insertion_point=insertion_point)

def run_range_async(insertion_point):
    import vim  # type: ignore

    p = getconfig("marker_prefix")
    m_cell = p + getconfig("marker_cell")
    m_value = p + getconfig("marker_value")
    m_stdout = p + getconfig("marker_stdout")
    m_stderr = p + getconfig("marker_stderr")
    m_magic = p + getconfig("marker_magic")

    range_ = vim.current.range
    debug(f"RANGE {range_.start} {range_.end}")

    unindent = True

    code = ""
    magics = []
    indentation = None
    for line in range_[1:]:
        l = line.strip()
        if l.startswith(m_magic):
            rest = l[len(m_magic) :]
            magics.extend(x.strip() for x in rest.split())

        if l.startswith(p):
            continue

        if unindent:
            if indentation is None and line.strip():
                m = re.match(r'^(\s*)[^\s].*$', line)
                indentation = m.groups()[0] if m is not None else ""
            if indentation is not None:
                if line.startswith(indentation):
                    line = line[len(indentation):]

        code += line + "\n"

    cell = Cell()
    cell.code = code

    _interpreter.execute(cell, magics=magics)

    # Find insertion position: before the first cell boundary that is not in the first line
    # default to end
    # insertion_point = -1
    # for i, line in enumerate(range_[:]):
        # debug(f"LINE {i} {line}")
        # if line.strip().startswith(m_cell):
            # insertion_point = i + 1
            # break

    _interpreter.wait_result(cell, range_, insertion_point)


    if getconfig("expand_marker") and insertion_point >= 0:
        range_[insertion_point] = cell.format_marker()

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

