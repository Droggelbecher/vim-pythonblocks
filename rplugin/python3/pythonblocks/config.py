
import pynvim

_DEFAULT_CONFIG = {
    'marker_cell': '#==',
    'marker_stdout': '#=|',
    'marker_stderr': '#=!',
    'marker_value': '#=>',
    'template_marker': ' {computed_at:%H:%M:%S} {dt:60.2f}',
    'template_computing': ' {computed_at:%H:%M:%S} Computing {dt:50.2f}',
    'update_interval': 0.1,
}

def get(c, type_=str):
    from .plugin import _nvim
    try:
        return type_(_nvim.eval(f"pythonblocks#{c}"))
    except pynvim.api.common.NvimError:
        return type_(_DEFAULT_CONFIG[c])
