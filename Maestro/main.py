
from config import utelegram_config
from config import wlan_com
from config import disp_conf

from machine import reset

import utelegram
import time
import gc
import hardware
import espnow

print('Iniciando bot')
bot = utelegram.ubot(utelegram_config['token'], True)
bot.saluda(utelegram_config['chat_id_default'])
rele = hardware.rele() # relé utilizado para hacer saltar al diferencial
sensor_st = hardware.sensor()  # sensor del estudio
dir_sensor_tx = wlan_com.get('mac_sensortx')
e = espnow.ESPNow()
e.active(True)
e.add_peer(dir_sensor_tx)

while True:
    print('bot en escucha')
    if bot.read_once():

        # Analiza el comando recibido y responde
        if bot.command == '/ping':
            bot.reply_ping(bot.chat_id)

        elif bot.command == '/temp':
            # Obtiene los valores de temperatura y humedad del sensor cableado (estudio)
            sensor_st.update_values()
            bot.send(bot.chat_id, f'Estudio: Temperatura: {sensor_st.get_temp()} - Humedad: {sensor_st.get_hum()}')
            
            # Se solicitan al dispositivo ESP01 por wifi que devuelva los datos del sensor
            # ubicados en la planta transmisora.
            print("Solicitando datos al sensor del transmisor")
            e.send(dir_sensor_tx, "values")
            host, msg = e.recv(timeout_ms=3000)
            if msg:
                data = msg.decode('utf-8').split(',')
                print(f'Datos recibidos de sensor del transmisor {data}')
                temp = data[0]
                hum = data[1]
                bot.send(bot.chat_id, f'Transmisor: Temperatura: {temp}° - Humedad: {hum}%')
            else:
                print('No hay comunicacion con sensor de transmisor')
                print(e.stats())
                bot.send(bot.chat_id, "No puedo obtener los datos del transmisor")
    
        elif bot.command == '/apagar':
            # se activa relé que pone a tierra el vivo de la red de 220V.
            print('Ejecutando apagado de emergencia')
            bot.send(bot.chat_id, "Ok, vamos a cortar la energía")
            if rele.shutdown():
                bot.send(bot.chat_id, "Se ha cortado la energía")
            else:
                bot.send(bot.chat_id, "Parece que no lo he logrado")

        elif bot.command == '/saluda':
            print('Saludando a pedido')
            bot.send(bot.chat_id, f'Hola {bot.chat_name}, saludos!')

        elif bot.command == '/reset':
            print('Reinicio de dispositivo')
            bot.send(bot.chat_id, f'Ok, voy a reiniciarme en {disp_conf['reset_delay']} segundos.')
            time.sleep(disp_conf['reset_delay'])
            reset()

    time.sleep(3)
    gc.collect()
