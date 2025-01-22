import espnow
import dht
from machine import Pin
import gc
import asyncio
from config import wlan_com

print('Configurando pines')
rele = Pin(4,Pin.OUT)
sensor = dht.DHT11(Pin(5, Pin.IN))

async def rele_control():
      while True:
            sensor.measure()
            temp = sensor.temperature()
            print(f'Temperatura: {temp}')
            if temp > 28:
                #enciende ventilador
                rele.value(1)
            elif temp < 28:
                rele.value(0)
            await asyncio.sleep(6)    

async def msg_control():
    e = espnow.ESPNow()
    e.active(True)
    master = b'\xff\xff\xff\xff\xff\xff'
    print('Escuchando')
    while True:
        host, msg = e.recv(timeout_ms=100)
        if msg:
            print('Recibiendo mensaje')
            if msg.decode('utf-8') == 'values':
                print('Solicitud de valores')
                sensor.measure()
                temp = sensor.temperature()
                hum = sensor.humidity()
                print(f'Enviando datos - Temp: {temp}° - Hum: {hum}%')
                resp = str(temp) + ',' + str(hum)
                e.send(master, resp)
                print(f'Datos enviado: {resp}')
            else:
                print(f'Mensaje no válido - {msg.decode('utf-8')}')
        gc.collect()
        await asyncio.sleep(0)

async def main():
    # Ejecuta las dos tareas de forma asincrónica
    print('creando tarea rele')
    asyncio.create_task( rele_control())
    print('creando tarea espnow')
    asyncio.create_task(msg_control())
    while True:
        await asyncio.sleep(1)

print('Corriendo tarea')
asyncio.run(main())