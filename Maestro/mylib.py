import sys
import time


DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

_LEVEL_NAMES = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

_console_enabled = True
_log_enabled = False
_log_directory = None
_log_date = None
_log_filename = None
_utc_offset = 0
_pending = []
_MAX_PENDING = 50


def configure_output(debug, logging_enabled):
    global _console_enabled, _log_enabled
    global _log_directory, _pending

    _console_enabled = debug
    _log_enabled = logging_enabled

    if not _log_enabled:
        _log_directory = None
        _pending = []


def emergency_print(*values):
    print(*values)


def disable_logging():
    global _log_enabled, _log_directory, _pending
    _log_enabled = False
    _log_directory = None
    _pending = []


def _write_log(level, message, exception=None):
    global _log_date, _log_filename

    tm = time.localtime(time.time() + _utc_offset)
    date = (tm[0], tm[1], tm[2])
    if date != _log_date:
        separator = "" if _log_directory.endswith("/") else "/"
        _log_filename = "{}{}{:02d}-{:02d}-{:04d}.log".format(
            _log_directory, separator, tm[2], tm[1], tm[0]
        )
        _log_date = date

    index = level // 10 - 1
    level_name = (
        _LEVEL_NAMES[index]
        if level % 10 == 0 and 0 <= index < len(_LEVEL_NAMES)
        else str(level)
    )
    line = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}:{}:bot-radio:{}\n".format(
        tm[0], tm[1], tm[2], tm[3], tm[4], tm[5], level_name, message
    )

    try:
        with open(_log_filename, "a") as file:
            file.write(line)
            if exception is not None:
                sys.print_exception(exception, file)
    except Exception as error:
        emergency_print("Error al escribir el log:", repr(error))
        emergency_print("Logging fallback:", line.rstrip())
        if exception is not None:
            sys.print_exception(exception, sys.stderr)


def configure_logging(directory, utc_offset=0):
    global _log_directory, _log_date, _log_filename, _utc_offset, _pending

    if not _log_enabled:
        _pending = []
        return

    _log_directory = directory.rstrip("/") or "/"
    _log_date = None
    _log_filename = None
    _utc_offset = utc_offset

    pending = _pending
    _pending = []
    for level, message in pending:
        _write_log(level, "[PRE-NTP] " + message)


def log_print(*values, level=INFO, exception=None):
    message = " ".join(str(value) for value in values)

    if _console_enabled:
        print(*values)

    if not _log_enabled or level < INFO:
        return

    if _log_directory is None:
        if exception is not None:
            message = message + " | " + repr(exception)
        if len(_pending) >= _MAX_PENDING:
            _pending.pop(0)
        _pending.append((level, message))
        return

    _write_log(level, message, exception)


def formatTime(time, offset):
    t = time.localtime(time.time() + offset)
    datetime = "{:02d}/{:02d}/{:04d} - {:02d}:{:02d}:{:02d}".format(
        t[2],  # dia
        t[1],  # mes
        t[0],  # anio
        t[3],  # hora
        t[4],  # minuto
        t[5]   # segundo
    )
    return datetime
