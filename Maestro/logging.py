import sys
import time


CRITICAL = const(50)
ERROR = const(40)
WARNING = const(30)
INFO = const(20)
DEBUG = const(10)

_LEVEL_NAMES = {
    CRITICAL: "CRITICAL",
    ERROR: "ERROR",
    WARNING: "WARNING",
    INFO: "INFO",
    DEBUG: "DEBUG",
}

_destination = None
_daily = False
_date = None
_filename = None
_utc_offset = 0
_level = INFO
_logger = None


def _localtime():
    return time.localtime(time.time() + _utc_offset)


def _resolve_filename(tm):
    global _date, _filename

    if _destination is None or not _daily:
        return _destination

    date = (tm[0], tm[1], tm[2])
    if date != _date:
        directory = _destination.rstrip("/") or "/"
        separator = "" if directory.endswith("/") else "/"
        _filename = "{}{}{:02d}-{:02d}-{:04d}.log".format(
            directory, separator, tm[2], tm[1], tm[0]
        )
        _date = date

    return _filename


class Logger:
    def __init__(self, name):
        self.name = name

    def log(self, level, message):
        if level < _level:
            return None

        tm = _localtime()
        line = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}:{}:{}:{}\n".format(
            tm[0], tm[1], tm[2], tm[3], tm[4], tm[5],
            _LEVEL_NAMES.get(level, str(level)), self.name, message,
        )
        filename = _resolve_filename(tm)

        if filename is None:
            sys.stderr.write(line)
            return None

        try:
            with open(filename, "a") as file:
                file.write(line)
            return filename
        except OSError as error:
            print("--- Logging Storage Error ---")
            print(repr(error))
            sys.stderr.write(line)
            return None

    def exception(self, exception, message):
        filename = self.log(ERROR, message)
        if filename is None:
            sys.print_exception(exception, sys.stderr)
            return

        try:
            with open(filename, "a") as file:
                sys.print_exception(exception, file)
        except OSError as error:
            print("--- Logging Storage Error ---")
            print(repr(error))
            sys.print_exception(exception, sys.stderr)


def basicConfig(level=INFO, filename=None, filemode="a", format=None,
                daily=False, utc_offset=0):
    global _destination, _daily, _date, _filename, _utc_offset, _level

    if daily and filename is None:
        raise ValueError("filename must be a directory when daily is enabled")

    _destination = filename
    _daily = daily
    _date = None
    _filename = None
    _utc_offset = utc_offset
    _level = level

    if filename is not None and filemode != "a":
        target = _resolve_filename(_localtime())
        with open(target, "w"):
            pass


def getLogger(name="root"):
    global _logger

    if _logger is None or _logger.name != name:
        _logger = Logger(name)
    return _logger
