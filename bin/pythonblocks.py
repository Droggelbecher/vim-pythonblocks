
from multiprocessing import Process, Pipe
from typing import Union, Optional, Set, Tuple
import sys
import traceback
import time
import datetime

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
        t = time.time()
        ret = self._run(globals_, locals_)
        dt = time.time() - t

        if ret is not None:
            ret = repr(ret)

        values = {}
        for k in self.evals:
            try:
                values[k] = repr(eval(k, globals_, locals_))
            except Exception as e:
                values[k] = 'raised ' + e.__class__.__name__ + ': ' + str(e)

        return ret, values, dt

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
            return_value, values, dt = command(globals_)
        except Exception as e:
            sys.stderr.write(traceback.format_exc())

        connection.send({
            'stdout': sys.stdout.getvalue(),
            'stderr': sys.stderr.getvalue(),
            'values': values,
            'return_value': return_value,
            'dt': dt
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
        print(f"[pythonblocks] Python subprocess restarted")

    def exec(self, cell):
        try:
            self.connection.send(ExecCommand(cell.code, evals=cell.expressions))
        except Exception as e:
            sys.stderr.write(traceback.format_exc())
            # Subprocess died. Try *once* per call command to restart it
            self.restart()
            self.connection.send(ExecCommand(cell.code, evals=cell.expressions))

        d = self.connection.recv()
        for k, v in d.items():
            setattr(cell, k, v)
        return cell


class Cell:
    code = ""
    expressions = ()

    return_value = None
    values = {}
    stdout = []
    stderr = []
    dt = None

    @classmethod
    def from_range(class_, range_):
        c = class_()
        c.code = "\n".join(range_[:])
        return c


_interpreter = None
def init():
    global _interpreter
    _interpreter = SubprocessInterpreter()


# _markers = {
    # 'prefix': '#=',
    # 'cell': '=',
    # 'value': '>',
    # 'stdout': '|',
    # 'stderr': '!',
# }

# _suppress_none_return = True
# _insert_return = 'not_none'
# _marker_template = "{dt:>74}s "

# _config = {
    # 'marker_prefix': '#=',
    # 'marker_cell': '=',
    # 'marker_value': '>',
    # 'marker_stdout': '|',
    # 'marker_stderr': '!',
    # 'expand_marker': 1,
    # 'marker_template': '{dt:>74}s ',
    # 'insert_return': 'not_none',
# }

def getconfig(c, type_=str, default=None):
    import vim
    return vim.vars.get('pythonblocks#' + c, default)
    # import vim
    # global _config

    # for k in tuple(_config.keys()):
        # _config[k] = vim.vars.get('pythonblocks#' + k, _config[k])

    # global _markers, _insert_return, _marker_template
    # _markers['prefix'] = vim.vars.get('pythonblocks#marker_prefix', '#=')
    # _markers['cell'] = vim.vars.get('pythonblocks#marker_cell', '=')
    # _markers['value'] = vim.vars.get('pythonblocks#marker_value', '>')
    # _markers['stdout'] = vim.vars.get('pythonblocks#marker_stdout', '|')
    # _markers['stderr'] = vim.vars.get('pythonblocks#marker_stderr', '!')

    # _insert_return = vim.vars.get('pythonblocks#

    # _marker_template = vim.vars.get('pythonblocks#marker_template', '{dt:>74}s ')

def restart():
    _interpreter.restart()

def format_marker(cell):
    m_cell = getconfig('marker_prefix') + getconfig('marker_cell')
    template = getconfig('marker_template')

    value = cell.return_value
    oneline_value = value.splitlines()[0] if isinstance(value, str) else value

    return m_cell + " " + template.format(**{
        'dt': cell.dt,
        'value': oneline_value,
        'value_unless_none': oneline_value if oneline_value is not None else '',
        'time': datetime.datetime.now(),
    })

def run_range():
    import vim
    global _markers

    m_cell = getconfig('marker_prefix') + getconfig('marker_cell')
    m_value =  getconfig('marker_prefix') + getconfig('marker_value')
    m_stdout = getconfig('marker_prefix') + getconfig('marker_stdout')
    m_stderr = getconfig('marker_prefix') + getconfig('marker_stderr')

    range_ = vim.current.range
    cell = Cell.from_range(range_)
    _interpreter.exec(cell)

    # Find insertion position: before the first cell boundary that is not in the first line
    # default to end
    insertion_point = -1
    for i, line in enumerate(range_[1:]):
        if line.startswith(m_cell):
            insertion_point = i + 1
            break

    if getconfig('expand_marker') and insertion_point >= 0:
        range_[insertion_point] = format_marker(cell)

    l = []

    if getconfig('insert_stdout'):
        for out in cell.stdout.splitlines():
            l.append(f"{m_stdout} {out}")

    if getconfig('insert_stderr'):
        for err in cell.stderr.splitlines():
            l.append(f"{m_stderr} {err}")

    # if not _suppress_none_return or cell.return_value is not None:
    c = getconfig('insert_return')
    if ((c == 'not_none') and (cell.return_value is not None)) or c == True:
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

init()

