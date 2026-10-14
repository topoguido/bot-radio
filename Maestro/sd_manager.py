from machine import SDCard
import uos


def mount(cs, mosi, miso, sck):
    sd = None
    try:
        sd = SDCard(slot=2, cs=cs, mosi=mosi, miso=miso, sck=sck)
        uos.mount(sd, "/sd")
        return sd
    except Exception as error:
        print("Error al inicializar la tarjeta SD:", error)
        if sd is not None:
            try:
                sd.deinit()
            except Exception:
                pass
        return None
