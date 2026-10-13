from machine import ADC, Pin, SDCard
import dht
import mylib
from time import sleep, ticks_ms, ticks_diff, sleep_us
from math import sqrt
import uos

class sensor:
    
    def __init__(self, pin, mode=Pin.IN):
        self.sensor_temp = dht.DHT11(Pin(pin))
        self._temp = None
        self._hum = None
    
    def update_values(self):
        try:
            self.sensor_temp.measure()
            sleep(0.5)
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
    def __init__(self, pin, mode=Pin.OUT):
        self.rele = Pin(pin, mode)

    def shutdown(self):
        self.rele.value(1)
        sleep(0.5)
        self.rele.value(0)
        return True
    
class releContac:
    def __init__(self, pin, mode=Pin.OUT):
        self.rele = Pin(pin, mode)

    def changeStatus(self):
        self.rele.value(1)
        sleep(0.5)
        self.rele.value(0)
        return True
    
    def status(self):
        return self.rele.value()


class releCarga:
     def __init__(self, Vmin, Vmax, debug, pin, mode=Pin.OUT):
        self.rele = Pin(pin, mode, value=0)
        self.Vmax = Vmax
        self.Vmin = Vmin
        self.debug = debug
     
     def on(self):
         self.rele.value(1)
         mylib.log_print("Cargador encendido", level=mylib.DEBUG)
         return True

     def off(self):
          self.rele.value(0)
          mylib.log_print("Cargador apagado", level=mylib.DEBUG)
          return True
    
     def status(self):
        mylib.log_print(
            f"Estado cargador: {self.rele.value()}",
            level=mylib.DEBUG,
        )
        return self.rele.value()

     def checkCarga(self, value):
        if value >= (self.Vmax):
             #apaga
            mylib.log_print(f"Tension bateria: {value}", level=mylib.DEBUG)
            mylib.log_print("Apagando cargador", level=mylib.DEBUG)
            self.off()
            return False
        
        if value < self.Vmin:
            # enciende
            mylib.log_print(f"Tension bateria: {value}", level=mylib.DEBUG)
            mylib.log_print("Encendiendo cargador", level=mylib.DEBUG)
            self.on()
            return True
         
          
        
        
class ACSensor:
    def __init__(self, pinIn, pinOut, mode=Pin.IN):
          self.sensorIn = ADC(Pin(pinIn))
          self.sensorIn.atten(ADC.ATTN_11DB)
          self.sensorOut = ADC(Pin(pinOut))
          self.sensorOut.atten(ADC.ATTN_11DB)
          self.umbralIn = 100
          self.umbralOut = 100
          self.factorIn = 232.0/700
          self.factorOut = 232.0/248

 
    def leer_rms_adc(self, adc, duracion_ms=1000):
        cantidad = 0
        suma = 0
        suma_cuadrados = 0
        minimo = 4095
        maximo = 0
        inicio = ticks_ms()

        while ticks_diff(ticks_ms(), inicio) < duracion_ms:
            lectura = adc.read()
            cantidad += 1
            suma += lectura
            suma_cuadrados += lectura * lectura
            minimo = min(minimo, lectura)
            maximo = max(maximo, lectura)
            sleep_us(200)

        promedio = suma / cantidad
        varianza = suma_cuadrados / cantidad - promedio * promedio
        rms = sqrt(max(varianza, 0))

        return rms, promedio, minimo, maximo

    def getStatusAC_In(self):
        rms_adc, promedio, minimo, maximo = self.leer_rms_adc(self.sensorIn)
        hay_tension = rms_adc >= self.umbralIn
        tension_ac = rms_adc * self.factorIn if hay_tension else 0.0

        return tension_ac, hay_tension

    def getStatusAC_Out(self):
            rms_adc, promedio, minimo, maximo = self.leer_rms_adc(self.sensorOut)
            hay_tension = rms_adc >= self.umbralOut
            tension_ac = rms_adc * self.factorOut if hay_tension else 0.0
    
            return tension_ac, hay_tension

class DCSensor:
     
     def __init__(self, pin, mode=Pin.IN):
          self.sensorDC = ADC(Pin(pin))
          self.sensorDC.atten(ADC.ATTN_11DB)
          self.sensorDC.width(ADC.WIDTH_12BIT)
          self.factor_divisor_dc = 5


     def leer_tension_dc(self,adc, muestras=100):
        suma_uv = 0

        for _ in range(muestras):
            suma_uv += adc.read_uv()
            sleep_us(200)

        tension_pin = suma_uv / muestras / 1_000_000
        tension_medida = tension_pin * self.factor_divisor_dc

        return tension_medida


     def getStatus(self):
        return self.leer_tension_dc(self.sensorDC)

class MySDCard:
    def __init__(self, cs_pin, mosi_pin, miso_pin, sck_pin):
        self.cs = cs_pin
        self.mosi = mosi_pin
        self.miso = miso_pin
        self.sck = sck_pin
        self.sd = None

    def init(self):
        try:
            self.sd = SDCard(
                slot=2,
                cs=self.cs,
                mosi=self.mosi,
                miso=self.miso,
                sck=self.sck,
            )
            uos.mount(self.sd, "/sd")
            return True
        except Exception as e:
            mylib.emergency_print("Error al inicializar la tarjeta SD:", e)
            return False

    def deinit(self):
        try:
            uos.umount("/sd")
            self.sd.deinit()
            self.sd = None
            return True
        except Exception as e:
            mylib.emergency_print("Error al desmontar la tarjeta SD:", e)
            return False

    def write_file(self, filename, data):
        try:
            with open("/sd/" + filename, "a") as f:
                f.write(data + "\n")
            return True
        except Exception as e:
            mylib.emergency_print("Error al escribir en el archivo:", e)
            return False
