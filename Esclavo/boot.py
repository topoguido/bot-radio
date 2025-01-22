import network
import ubinascii

print('Iniciando')
wlan = network.WLAN(network.WLAN.IF_AP) # network.WLAN.IF_STA | network.WLAN.IF_AP
wlan.config(pm=wlan.PM_NONE, channel=8)
wlan.active(True)
wlan_mac = wlan.config("mac")
print(f'Mi MAC: {ubinascii.hexlify(wlan_mac).decode()} - {wlan_mac}')
