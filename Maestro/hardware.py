from machine import Pin
import dht
from time import sleep

class sensor:
    
    def __init__(self):
        self.sensor_temp = dht.DHT11(Pin(1, Pin.IN))
        self._temp = None
        self._hum = None
    
    def update_values(self):
        try:
            self.sensor_temp.measure()
            self._temp = self.sensor_temp.temperature()
            self._hum  = self.sensor_temp.humidity()
            return True
        
        except Exception:
            self._temp = None
            self._hum = None
            return False
        
    def get_temp(self):
            return self._temp
        
    
    def get_hum(self):
            return self._hum
        
    
class releDif:
    def __init__(self):
        self.rele = Pin(2, Pin.OUT)

    def shutdown(self):
        self.rele.value(1)
        sleep(0.5)
        self.rele.value(0)
        return True
    
class releContac:
    def __init__(self):
        self.rele = Pin(4, Pin.OUT)
        #self.rele.value(0)

    def on(self):
        self.rele.value(1)
        return True
    
    def off(self):
        self.rele.value(0)
        return True
    
    def status(self):
        return self.rele.value()
        
        
    
    