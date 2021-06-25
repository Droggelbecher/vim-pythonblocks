
from datetime import datetime

ENABLED = True

def debug(s):
    if not ENABLED:
        return

    with open("/tmp/pythonblocks.log", "a") as f:
        f.write(f"{datetime.now():%Y%m%d %H:%M:%S} {s}\n")

