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


def _format_log(timestamp, level, message):
    global _log_date, _log_filename

    tm = time.localtime(timestamp + _utc_offset)
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
    return _log_filename, line


def configure_logging(directory, utc_offset=0):
    global _log_directory, _log_date, _log_filename, _utc_offset, _pending

    if not _log_enabled:
        _pending = []
        return

    _log_directory = directory.rstrip("/") or "/"
    _log_date = None
    _log_filename = None
    _utc_offset = utc_offset

    timestamp = time.time()
    for index, entry in enumerate(_pending):
        if entry[0] is None:
            _pending[index] = (
                timestamp,
                entry[1],
                "[PRE-NTP] " + entry[2],
            )


def log_print(*values, level=INFO, exception=None):
    message = " ".join(str(value) for value in values)

    if _console_enabled:
        print(*values)

    if not _log_enabled or level < INFO:
        return

    if exception is not None:
        message = message + " | " + repr(exception)

    if len(_pending) >= _MAX_PENDING:
        _pending.pop(0)

    timestamp = time.time() if _log_directory is not None else None
    _pending.append((timestamp, level, message))


def has_pending_logs():
    return bool(_log_enabled and _log_directory is not None and _pending)


def flush_logging():
    global _pending

    if not has_pending_logs():
        return True

    pending = _pending
    _pending = []

    file = None
    open_filename = None
    current_line = None
    success = True

    try:
        for timestamp, level, message in pending:
            filename, current_line = _format_log(timestamp, level, message)
            if filename != open_filename:
                if file is not None:
                    file.close()
                    file = None
                file = open(filename, "a")
                open_filename = filename
            file.write(current_line)
    except Exception as error:
        emergency_print("Error al escribir el log:", repr(error))
        if current_line is not None:
            emergency_print("Logging fallback:", current_line.rstrip())
        success = False
    finally:
        if file is not None:
            try:
                file.close()
            except Exception as error:
                emergency_print("Error al cerrar el log:", repr(error))
                success = False

    return success


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
