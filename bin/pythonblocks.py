
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


    def __call__(self, globals_, locals_=None):
        ret = self._run(globals_, locals_)
        if ret is not None:
            ret = repr(ret)

        values = {}
        for k in self.evals:
            try:
                values[k] = repr(eval(k, globals_, locals_))
            except Exception as e:
                values[k] = 'raised ' + e.__class__.__name__ + ': ' + str(e)

        return ret, values

class ExitCommand:
    pass


def execution_loop(connection):
    """
    Back-end (actual subprocess)
    """
    globals_ = {}

    import sys
    import io

    while True:
        command = connection.recv()
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        return_value = None
        values = {}

        if isinstance(command, ExitCommand):
            break

        try:
            return_value, values = command(globals_)
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

    def restart(self):
        self.connection.send(ExitCommand())
        self.subprocess.join(timeout=5000)
        if self.subprocess.is_alive():
            self.subprocess.kill()
        self.subprocess.close()

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

def restart():
    _interpreter.restart()


def run_range():
    import vim
    global _markers
    update_config()

    range_ = vim.current.range
    cell = Cell.from_range(range_)
    _interpreter.exec(cell)

    # Find insertion position: before the first cell boundary that is not in the first line
    # default to end
    insertion_point = -1
    for i, line in enumerate(range_[1:]):
        if line.startswith(f"{_markers['prefix']}{_markers['cell']}"):
            insertion_point = i + 1
            break


    l = []

    m_value = _markers['prefix'] + _markers['value']
    m_stdout = _markers['prefix'] + _markers['stdout']
    m_stderr = _markers['prefix'] + _markers['stderr']

    if not _suppress_none_return or cell.return_value is not None:
        for line in cell.return_value.splitlines():
            l.append(f"{m_value} {line}")

    for k, v in tuple(cell.values.items()):
        lines = v.splitlines()
        l.append(f"{m_value} {k} = {lines[0]}")
        for line in lines[1:]:
            l.append(f"{m_value} ...{' ' * len(k)}{line}")

    for out in cell.stdout.splitlines():
        l.append(f"{m_stdout} {out}")

    for err in cell.stderr.splitlines():
        l.append(f"{m_stderr} {err}")

    if insertion_point >= 0:
        range_.append(l, insertion_point)
    else:
        range_.append(l)

init()
print(f"PIM Module loaded on python version {sys.version}")

