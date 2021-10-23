
from .ipc import Reader, Writer
from pythonblocks import logging_ as logging
logging.basicConfig(filename="/tmp/pythonblocks_executor.log", level=logging.DEBUG)
_log = logging.getLogger(__name__)

_writer = None
_reader = None

_setup_code = """
def _run_cell_magic(magic, block):
    import pyblocks
    return pyblocks.run_cell_magic(magic, block)
"""

def exec_magic_block(magic, code, globals_):
    code2 = '_ = _run_cell_magic("' + magic + '", """' + code + '""")'
    t = time.time()
    exec(code2, globals_)
    ret = eval('_', globals_)
    dt = time.time() - t
    return ret, dt

def exec_block(code, globals_, eval_last_expr=True):
    """
    Args:
        code: python code
        globals_: dict of globals
        eval_last_expr: if True and last statement is an expresssion, return value of that expression

    Return:
        tuple (return value or None, exec time in s)
    """
    ret = None
    dt = 0.0

    # Split off last statement and see if its an expression.
    # if it is, execute it separately with eval() so we can obtain its value
    statements = list(ast.iter_child_nodes(ast.parse(code)))
    if not statements:
        return ret, dt

    if eval_last_expr and isinstance(statements[-1], ast.Expr):
        # use `ast.parse` instead of `ast.Module` for better portability
        # python3.8 changes the signature of `ast.Module`
        module = ast.parse("")
        module.body = statements[:-1]
        module = ast.fix_missing_locations(module)

        exec_part = compile(module, filename="<ast>", mode="exec")
        eval_part = compile(
            ast.Expression(body=statements[-1].value), filename="<ast>", mode="eval"
        )

        t = time.time()
        exec(exec_part, globals_)
        ret = eval(eval_part, globals_)
        dt = time.time() - t

    else:
        t = time.time()
        exec(code, globals_)
        dt = time.time() - t

    return ret, dt

def execution_loop():
    globals_ = {}

    exec(_setup_code, globals_)

    while True:
        command = _reader()
        _log.debug(f"Received command: {command}")
        if command is None:
            time.sleep(0.1)
            continue

        type_ = command.get("type", "exit")
        code = command.get("code", "")
        magics = command.get("magics", [])

        if type_ == "exit":
            break

        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        return_value = None
        dt = 0.0

        try:
            if len(magics):
                r = code
                for magic in magics:
                    r, ddt = exec_magic_block(magic, str(r), globals_)
                    dt += ddt
                return_value = r
            else:
                return_value, dt = exec_block(code, globals_, eval_last_expr)
        except Exception as e:
            sys.stderr.write(traceback.format_exc())

        _writer(
            {
                "stdout": sys.stdout.getvalue(),
                "stderr": sys.stderr.getvalue(),
                "return_value": repr(return_value) if return_value is not None else None,
                "dt": dt,
            },
        )


if __name__ == '__main__':
    _writer = Writer(sys.stdout.fileno())
    _reader = Reader(sys.stdin.fileno())

    _log.debug(f"Executor started {_reader} {_writer}")

    try:
        execution_loop()
    except Exception:
        f = open('/tmp/pythonblocks_executor_crash.log', 'w')
        f.write(traceback.format_exc())
        f.close()
