from config import wifi_config
import network
import ubinascii

wlan = network.WLAN(network.WLAN.IF_STA)
if not wlan.isconnected():
    wlan.active(True)
    wlan.config(channel=8, pm=wlan.PM_NONE)
    wlan.connect(wifi_config['ssid'], wifi_config['password'])
    wlan_mac = wlan.config("mac")
    print(f'Mi MAC es: {ubinascii.hexlify(wlan_mac).decode()}')
    print(f'Esperando red - Parametros: SSID: {wifi_config['ssid']} Pass: {wifi_config['password']}')
    while not wlan.isconnected():
        pass
    if wlan.isconnected():
        print(f'conectado a red con IP {wlan.ipconfig("addr4")}')
