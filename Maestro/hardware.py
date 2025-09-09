from machine import Pin
import dht
from time import sleep

class sensor:
    
    def __init__(self):
        self.sensor_temp = dht.DHT11(Pin(1, Pin.IN))
    
    def update_values(self):
        self.sensor_temp.measure()
    
    def get_temp(self):
        return self.sensor_temp.temperature()
    
    def get_hum(self):
        return self.sensor_temp.humidity()
    
class releDif:
    def __init__(self):
        self.releDif = Pin(2, Pin.OUT)

    def shutdown(self):
        self.releDif.value(1)
        sleep(0.5)
        self.releDif.value(0)
        return True
    
class releContac:
    def __init__(self):
        self.releContac = Pin(4, Pin.OUT)

    def on(self):
        self.releContac.value(0)
        return True
    
    def off(self):
        self.releContac.value(1)
        return True
    
    def status(self):
        return self.releContac.value()
        
        
    
    