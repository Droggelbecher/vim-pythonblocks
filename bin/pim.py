
from multiprocessing import Process, Pipe
from typing import Union, Optional, Set, Tuple
import sys

class ExecCommand:
    """
    A command to be executed by the dedicated python interpreter process
    """
    def __init__(self, code, evals=()):
        self.code = code
        self.evals = evals

    def __call__(self, globals_, locals_):
        exec(self.code, globals_, locals_)
        r = {}
        for k in self.evals:
            try:
                r[k] = repr(eval(k, globals_, locals_))
            except Exception as e:
                r[k] = 'raised ' + e.__class__.__name__ + ': ' + str(e)
        return r


def execution_loop(connection):
    """
    Back-end (actual subprocess)
    """
    locals_ = {}
    globals_ = {}

    import sys
    import io

    while True:
        command = connection.recv()
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        values = {}
        try:
            values = command(globals_, locals_)
        except Exception as e:
            sys.stderr.write(e.__class__.__name__ + ': ' + str(e))

        connection.send({
            'stdout': sys.stdout.getvalue(),
            'stderr': sys.stderr.getvalue(),
            'values': values,
        })

class SubprocessInterpreter:
    """
    Front-end
    """
    def __init__(self):
        self.connection, conn_executor = Pipe()
        self.subprocess = Process(target=execution_loop, args=(conn_executor,))
        self.subprocess.start()

    def exec(self, cell):
        self.connection.send(ExecCommand(cell.code, evals=cell.expressions))
        d = self.connection.recv()
        for k, v in d.items():
            setattr(cell, k, v)
        # cell.__dict__.update(d)
        return cell


class Cell:
    _id = None # Identification of cell for text interface
    code = ""
    expressions = ()
    values = {}
    stdout = []
    stderr = []

    @classmethod
    def from_range(class_, range_):
        c = class_()
        c.code = "\n".join(range_[:])
        return c


_interpreter = None
def init():
    global _interpreter
    _interpreter = SubprocessInterpreter()


def run_current_cell():
    import vim
    row, col = vim.current.window.cursor
    cell = _text_interface.get_cell(row - 1, create=True)
    _interpreter.exec(cell)
    _text_interface.update_cell(cell)

_markers = {
    'prefix': '#=',
    'cell': '=',
    'value': '>',
    'stdout': '|',
    'stderr': '!',
}

def update_config():
    import vim
    global _markers
    _markers['prefix'] = vim.vars.get('pim#marker_prefix', '#=')
    _markers['cell'] = vim.vars.get('pim#marker_cell', '=')
    _markers['value'] = vim.vars.get('pim#marker_value', '>')
    _markers['stdout'] = vim.vars.get('pim#marker_stdout', '|')
    _markers['stderr'] = vim.vars.get('pim#marker_stderr', '!')

def run_range():
    import vim
    global _markers
    update_config()

    range_ = vim.current.range
    cell = Cell.from_range(range_)
    _interpreter.exec(cell)

    # Find insertion position: before the first cell boundary that is not in the first line
    # default to end
    insertion_point = len(range_) - 1
    for i, line in enumerate(range_[1:]):
        if line.startswith(f"{_markers['prefix']}{_markers['cell']}"):
            insertion_point = i + 1
            break

    for err in cell.stderr.splitlines()[::-1]:
        range_.append(f"{_markers['prefix']}{_markers['stderr']} {err}", insertion_point)
    for out in cell.stdout.splitlines()[::-1]:
        range_.append(f"{_markers['prefix']}{_markers['stdout']} {out}", insertion_point)

init()
print(f"PIM Module loaded on python version {sys.version}")

