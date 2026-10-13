from machine import reset
import network
import ubinascii
import senko
import mylib
from Configurations import Configurations

configs = Configurations("boot")
mylib.configure_output(configs.debug, configs.logging_status)

wlan = network.WLAN(network.WLAN.IF_STA)
if not wlan.isconnected():
    wlan.active(True)
    wlan.config(pm=wlan.PM_NONE)
    wlan.connect(configs.wifi_ssid, configs.wifi_password)
    wlan_mac = wlan.config("mac")
    mylib.log_print(f'Mi MAC es: {ubinascii.hexlify(wlan_mac).decode()}')
    mylib.log_print(f'Esperando red - Parametros: SSID: {configs.wifi_ssid} Pass: {configs.wifi_password}')
    while not wlan.isconnected():
        pass
    if wlan.isconnected():
        mylib.log_print(f'conectado a red con IP {wlan.ipconfig("addr4")}')

        OTA = senko.Senko(user = configs.update_user,
                          repo = configs.update_repo,
                          branch = configs.update_branch, 
                          files = configs.update_files,
                          working_dir = configs.update_working_dir
                          )
        
        if configs.update_status:
            if OTA.update():
                mylib.log_print('Nueva version de soft')
                reset()
            else:
                mylib.log_print('Soft al dia')
