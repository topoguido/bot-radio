import time


DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

_debug_enabled = False


def configure_output(debug):
    global _debug_enabled
    _debug_enabled = debug


def log_print(*values, level=INFO, exception=None):
    if level == DEBUG:
        if not _debug_enabled:
            return
        prefix = "[DEBUG]"
    elif level == WARNING:
        prefix = "[WARN]"
    elif level == ERROR:
        prefix = "[ERROR]"
    elif level == CRITICAL:
        prefix = "[CRITICAL]"
    else:
        prefix = "[INFO]"

    print(prefix, *values)


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
