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