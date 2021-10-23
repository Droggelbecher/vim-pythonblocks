
_loggers = {}

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40

_levelname = {
    DEBUG: "DEBUG",
    INFO: "INFO",
    WARNING: "WARNING",
    ERROR: "ERROR"
}

class Logger:
    def __init__(self, name, parent=None):
        self.level = DEBUG
        self.name = name
        self.parent = parent
        self.handlers = []

    def debug(self, msg):
        self.log(DEBUG, msg)
    def info(self, msg):
        self.log(INFO, msg)
    def warning(self, msg):
        self.log(WARNING, msg)
    def error(self, msg):
        self.log(ERROR, msg)

    def log(self, level, msg, name=None):
        if name is None:
            name = self.name
        if level < self.level:
            return
        if self.hasHandlers():
            for handler in self.handlers:
                handler.handle(f"{_levelname[level]} {name} {msg}")
        elif self.parent is not None:
            self.parent.log(level, msg, name=name)

    def hasHandlers(self):
        return len(self.handlers) > 0
    def addHandler(self, handler):
        self.handlers.append(handler)

class FileHandler:
    def __init__(self, filename):
        self.filename = filename

    def handle(self, s):
        with open(self.filename, 'a') as f:
            f.write(s + "\n")

root = _loggers["root"] = Logger("root")

def getLogger(name):
    if name not in _loggers:
        _loggers[name] = Logger(name, parent=root)
    return _loggers[name]

def basicConfig(filename=None, level=None):
    if level is not None:
        root.level = level
    if filename is not None:
        root.addHandler(FileHandler(filename))


