

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

_console_enabled = True
_log_enabled = False
_logger = None
_pending = []
_MAX_PENDING = 50


def configure_output(debug, logging_enabled):
    global _console_enabled, _log_enabled
    global _logger, _pending

    _console_enabled = debug
    _log_enabled = logging_enabled

    if not _log_enabled:
        _logger = None
        _pending = []


def emergency_print(*values):
    print(*values)


def disable_logging():
    global _log_enabled, _logger, _pending
    _log_enabled = False
    _logger = None
    _pending = []


def set_logger(logger):
    global _logger, _pending

    _logger = logger
    if not _log_enabled:
        _pending = []
        return

    pending = _pending
    _pending = []
    for level, message in pending:
        try:
            _logger.log(level, "[PRE-NTP] " + message)
        except Exception as e:
            emergency_print("Error al vaciar la cola de logging:", repr(e))


def log_print(*values, level=INFO, exception=None):
    message = " ".join(str(value) for value in values)

    if _console_enabled:
        print(*values)

    if not _log_enabled or level < INFO:
        return

    if _logger is None:
        if exception is not None:
            message = message + " | " + repr(exception)
        if len(_pending) >= _MAX_PENDING:
            _pending.pop(0)
        _pending.append((level, message))
        return

    try:
        if exception is None:
            _logger.log(level, message)
        else:
            _logger.exception(exception, message)
    except Exception as e:
        emergency_print("Error en log_print:", repr(e))


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
