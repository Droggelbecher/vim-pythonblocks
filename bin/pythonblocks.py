
from multiprocessing import Process, Pipe
from typing import Union, Optional, Set, Tuple
import sys

class ExecCommand:
    """
    A command to be executed by the dedicated python interpreter process
    """
    def __init__(self, code, eval_last_expr=True, evals=()):
        self.code = code
        self.evals = evals
        self.eval_last_expr = eval_last_expr

    def _run(self, globals_, locals_):
        if self.eval_last_expr:
            # Split off last statement and see if its an expression.
            # if it is, execute it separately with eval() so we can obtain its value
            import ast
            statements = list(ast.iter_child_nodes(ast.parse(self.code)))
            if not statements:
                return None

            if isinstance(statements[-1], ast.Expr):
                exec_part = compile(ast.Module(body=statements[:-1]), filename="<ast>", mode="exec")
                eval_part = compile(ast.Expression(body=statements[-1].value), filename="<ast>", mode="eval")
                exec(exec_part, globals_, locals_)
                return eval(eval_part, globals_, locals_)

        exec(self.code, globals_, locals_)


    def __call__(self, globals_, locals_):
        ret = self._run(globals_, locals_)

        values = {}
        for k in self.evals:
            try:
                values[k] = repr(eval(k, globals_, locals_))
            except Exception as e:
                values[k] = 'raised ' + e.__class__.__name__ + ': ' + str(e)

        return ret, values


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
        return_value = None
        values = {}

        try:
            return_value, values = command(globals_, locals_)
        except Exception as e:
            sys.stderr.write(e.__class__.__name__ + ': ' + str(e))

        connection.send({
            'stdout': sys.stdout.getvalue(),
            'stderr': sys.stderr.getvalue(),
            'values': values,
            'return_value': return_value
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
        return cell


class Cell:
    _id = None # Identification of cell for text interface
    code = ""
    expressions = ()

    return_value = None
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

_suppress_none_return = True

def update_config():
    import vim
    global _markers
    _markers['prefix'] = vim.vars.get('pythonblocks#marker_prefix', '#=')
    _markers['cell'] = vim.vars.get('pythonblocks#marker_cell', '=')
    _markers['value'] = vim.vars.get('pythonblocks#marker_value', '>')
    _markers['stdout'] = vim.vars.get('pythonblocks#marker_stdout', '|')
    _markers['stderr'] = vim.vars.get('pythonblocks#marker_stderr', '!')

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

    # Note: these must happen in reverse order as they all are inserted before the same line
    for err in cell.stderr.splitlines()[::-1]:
        range_.append(f"{_markers['prefix']}{_markers['stderr']} {err}", insertion_point)
    for out in cell.stdout.splitlines()[::-1]:
        range_.append(f"{_markers['prefix']}{_markers['stdout']} {out}", insertion_point)
    for k, v in tuple(cell.values.items())[::-1]:
        range_.append(f"{_markers['prefix']}{_markers['value']} {k} = {v}", insertion_point)

    if not _suppress_none_return or cell.return_value is not None:
        range_.append(f"{_markers['prefix']}{_markers['value']} {cell.return_value}", insertion_point)

init()
print(f"PIM Module loaded on python version {sys.version}")

