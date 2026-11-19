import gc
import network
import time

from Configurations import Configurations


WIFI_TIMEOUT_MS = 30 * 1000


def log_info(*values):
    print("[INFO]", *values)


def log_warning(*values):
    print("[WARN]", *values)


def log_error(*values):
    print("[ERROR]", *values)


configs = Configurations("boot")
wlan = network.WLAN(network.WLAN.IF_STA)

if not wlan.active():
    wlan.active(True)

wlan.config(pm=wlan.PM_NONE)

if not wlan.isconnected():
    mac = wlan.config("mac")
    mac_text = "".join("{:02x}".format(value) for value in mac)
    log_info("Mi MAC es:", mac_text)
    log_info("Esperando red - SSID:", configs.wifi_ssid)

    wlan.connect(configs.wifi_ssid, configs.wifi_password)
    start = time.ticks_ms()

    while (
        not wlan.isconnected()
        and time.ticks_diff(time.ticks_ms(), start) < WIFI_TIMEOUT_MS
    ):
        time.sleep_ms(250)

    mac = None
    mac_text = None
else:
    log_info("Wi-Fi ya estaba conectado")

if wlan.isconnected():
    log_info("Conectado a red con IP", wlan.ipconfig("addr4"))
else:
    log_warning("No se pudo conectar a Wi-Fi; se omite la actualización OTA")

updated = False
ota_checked = False
ota = None

if wlan.isconnected() and configs.update_status:
    log_info("Buscando actualizaciones OTA")

    try:
        gc.collect()
        import senko

        ota = senko.Senko(
            user=configs.update_user,
            repo=configs.update_repo,
            branch=configs.update_branch,
            files=configs.update_files,
            working_dir=configs.update_working_dir,
        )

        configs = None
        gc.collect()
        log_info("Memoria libre antes de OTA:", gc.mem_free(), "bytes")

        updated = ota.update()
        ota_checked = True
    except Exception as error:
        log_error("Error durante la actualización OTA:", repr(error))
        log_warning("Se continúa con el software instalado")
    finally:
        ota = None
        gc.collect()

    if updated:
        log_info("Nueva versión de software instalada; reiniciando")
        from machine import reset

        reset()
    elif ota_checked:
        log_info("Software al día")
elif not configs.update_status:
    log_info("Actualizaciones OTA deshabilitadas")

configs = None
gc.collect()
log_info("Inicio de boot completado")
