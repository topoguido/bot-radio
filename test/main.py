import dht
from machine import Pin
from time import sleep

sensor = dht.DHT11(Pin(27))
sleep(2)

while True:
    try:
        sensor.measure()
        print(sensor.temperature(), sensor.humidity())
    except Exception as error:
        print(repr(error))
    sleep(2)