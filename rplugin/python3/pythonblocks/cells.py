
import threading
from typing import Optional, Tuple
from pathlib import Path
import time
from dataclasses import dataclass
from contextlib import suppress
from pythonblocks import logging_ as logging
from . import config
from . import marker
from .executor_client import ExecutorClient
import pynvim

_log = logging.getLogger(__name__)

_execution_lock = threading.Lock()

_executor_client = None

def _log_buffer(buffer):
    for i, line in enumerate(buffer):
        _log.debug(f"{i:2d} | {line}")

def get_executor():
    global _executor_client
    if _executor_client is None:
        _executor_client = ExecutorClient()
    return _executor_client

class ConcurrentExecutionException(RuntimeError):
    pass


@dataclass
class Cell:
    id_: str = ""
    code: str = ""
    magics: Tuple[str] = ()


def make_cell(range_) -> Cell:
    """
    Return the cells ID. If it doesnt have one, generate one and return that.
    """
    # TODO("extract magics and code, make actual cell object")
    from .plugin import _nvim

    cell = Cell()

    _log_buffer(range_)
    marker_pos = marker.find(range_)
    if marker_pos is None:
        cell.id_ = marker.make_id()
        _log.debug(f"No marker found in {range_.start},{range_.end} appending {cell.id_}")
        range_.append(marker.make_cell_string(cell.id_))
        marker_pos = len(range_) - 1
        _log_buffer(range_)
        _log.debug(f"New marker pos: {marker_pos}")
    else:
        cell.id_ = marker.parse_id(range_[marker_pos])
        _log.debug(f"Marker {cell.id_} found at {marker_pos}")

    magics = []
    i = None
    for i in range(marker_pos, 0, -1):
        m = get_magic(_nvim.current.buffer[i])
        if m is not None:
            magics.append(m)
        if marker.is_cell_marker(_nvim.current.buffer):
            break

    cell.magics = tuple(magics)

    # TODO: unindent code
    cell.code = ''.join(_nvim.current.buffer[i:marker_pos])

    return cell


def tidy_cell(cell_id: str):
    # TODO
    raise NotImplementedError


def execute_cell_async(range_):
    """
    Run the given cell asynchronously, raise ConcurrentExecutionException if a cell execution is
    already running.
    """

    has_lock = _execution_lock.acquire(blocking=False)
    if not has_lock:
        raise ConcurrentExecutionException("Another cell is currently being executed")

    cell = make_cell(range_)
    pynvim.async_call(_execute_cell, cell)

def execute_cell(range_):
    from .plugin import _nvim
    # 1. send range data to executor
    # 2. whenever a (partial) result comes in,
    #    find cell marker & insert
    # 3. whenever 100ms have passed, find cell marker & update it
    # 4. when a cell result comes in, find cell marker & update it. Release lock.

    # TODO: Timeout

    cell = make_cell(range_)

    get_executor().write({
        'type': 'exec',
        'code': cell.code,
        'magics': cell.magics,
    })

    update_interval = max(float(config.get("update_interval")), 0.1)
    buffer = _nvim.current.buffer

    t = time.time()
    while True:
        message = get_executor().read()
        marker_pos = marker.find(buffer, id_=cell.id_)
        _log_buffer(buffer)
        _log.debug(f"Marker pos: {marker_pos} message {message}")

        if message is not None:
            type_ = message["type"]
            if type_ == "done":
                break
            elif type_ in ("stdout", "stdin", "value"):
                line = marker.make_result_string(type_, message["result"])
                _log.debug(f"Appending at {marker_pos}: {line}")
                buffer.append(marker_pos, line)
                _log_buffer(buffer)

        line = marker.make_cell_string(cell.id_, dt=time.time() - t, computing=True)
        _log.debug(f"Updating marker at {marker_pos}: {line}")
        buffer[marker_pos] = line
        _log_buffer(buffer)
        time.sleep(update_interval)

    line = marker.make_cell_string(cell.id_, dt=time.time() - t, computing=False)
    _log.debug(f"Updating marker at {marker_pos}: {line}")
    buffer[marker_pos] = line
    _log_buffer(buffer)

    with suppress(RuntimeError):
        _execution_lock.release()



