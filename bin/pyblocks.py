
import sys
import subprocess
import ast

_magic_functions = {}

def register_cell_magic(fn):
    """
    Register the given function `fn` as cell magic function, for later retrieval with
    `run_cell_magic`. Can be used as a decorator.

    fn is expected to except 1 string argument (the code of block its applied to)
    and return some value that represents the evaluation result of that block.

    The function name will be used as the name for the magic.

    Args:
        fn: Function as described above.
    """
    _magic_functions[fn.__name__] = fn

def run_cell_magic(magic, block):
    """
    Args:
        magic (str): Name of the magic function to execute
        block (str): contents of the block to pass to the magic function.

    Return:
        Execution result of the magic function.

    Raise:
        KeyError if the magic function could not be found.
    """
    return _magic_functions[magic](block)

@register_cell_magic
def shell(block):
    """
    Run the given block in a subprocess shell and return the returncode of the shell subprocess.
    """
    c = subprocess.run(block, shell=True, capture_output=True)
    print(c.stdout.decode('utf-8'), end='')
    print(c.stderr.decode('utf-8'), file=sys.stderr, end='')
    return c.returncode if c.returncode else None

@register_cell_magic
def str(block):
    """
    Return the given block as stripped string.
    """
    return block.strip()

@register_cell_magic
def nop(block):
    """
    Ignore contents of block and return None.
    """
    return None
silent = nop

@register_cell_magic
def parse(block):
    """
    Parse the block using python ast module and return the result.
    """
    return ast.parse(block).body


