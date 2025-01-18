from config import wifi_config
import network
import ubinascii

sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    sta_if.active(True)
    sta_if.scan()
    sta_if.connect(wifi_config['ssid'], wifi_config['password'])
    print(f'Mi MAC es: {print(ubinascii.hexlify(sta_if('mac')).decode())}')
    print('Esperando red')
    while not sta_if.isconnected():
        pass
    if sta_if.isconnected():
        print(f'conectado a red con IP {sta_if.ipconfig("addr4")}')
