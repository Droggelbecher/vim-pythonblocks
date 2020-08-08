import ast
import pickle
import sys
import time
import io
import traceback

_setup_code = """
def _run_cell_magic(magic, block):
    import pyblocks
    return pyblocks.run_cell_magic(magic, block)
"""

def send_object(object_, filelike):
    bytes_ = pickle.dumps(object_)
    len_ = len(bytes_)
    len_bytes = bytes([
        (len_ >> (8*(3 - i))) & 0xff
        for i in range(4)
    ])
    filelike.write(len_bytes + bytes_)
    filelike.flush()

def receive_object(filelike):
    len_bytes = filelike.read(4)
    len_ = sum([
        x << (8*(3 - i))
        for i, x in enumerate(len_bytes)
    ])
    data_bytes = filelike.read(len_)
    return pickle.loads(data_bytes)

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
        command = receive_object(_real_stdin)
        type_ = command.get("type", "exit")
        code = command.get("code", "")
        magics = command.get("magics", [])
        eval_last_expr = command.get("eval_last_expr", True)

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

        send_object(
            {
                "stdout": sys.stdout.getvalue(),
                "stderr": sys.stderr.getvalue(),
                "return_value": repr(return_value) if return_value is not None else None,
                "dt": dt,
            },
            _real_stdout
        )


if __name__ == '__main__':
    try:
        _real_stdout = sys.stdout.buffer
        _real_stdin = sys.stdin.buffer
    except AttributeError:
        _real_stdout = sys.stdout
        _real_stdin = sys.stdin

    try:
        execution_loop()
    except Exception:
        f = open('/tmp/pythonblocks_executor.log', 'w')
        f.write(traceback.format_exc())
        f.close()
