import random
import string
import re
import datetime
from . import config
from typing import Optional, Tuple

def find(range_, id_=None) -> Optional[int]:
    cell_marker = config.get("marker_cell")
    for i, line in enumerate(range_[1:]):
        if line.strip().startswith(cell_marker):
            if id_ is None or parse_id(line) == id_:
                return i + 1
    return None

def is_cell_marker(line):
    cell_marker = config.get("marker_cell")
    return line.strip().startswith(cell_marker)

def get_magic(line):
    magic_marker = config.get("marker_magic")
    line = line.strip()
    if line.startswith(magic_marker):
        return line[len(magic_marker):].strip()
    return None

def make_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def make_cell_string(id_, *, dt=0, computed_at=None, computing:bool = False) -> Tuple[str, str]:
    cell_marker = config.get("marker_cell")
    template = config.get("template_computing" if computing else "template_marker")
    if computed_at is None:
        computed_at = datetime.datetime.now()
    return f"{cell_marker} [{id_}] " + template.format(dt=dt, computed_at=computed_at)

def make_result_string(type_, result):
    marker = config.get(f"marker_{type_}")
    return f"{marker} {result}"

_ID_RE = re.compile(r'\s*\[([a-zA-Z0-9]+)\].*')

def parse_id(s: str) -> str:
    cell_marker = config.get("marker_cell")
    s = s.strip()
    assert s.startswith(cell_marker)
    s = s[len(cell_marker):]

    m = _ID_RE.match(s)
    if m is None:
        raise ValueError(f"Marker string '{s}' does not contain a cell ID")
    return m.groups()[0]
