from machine import reset
import utelegram
import time
import ntptime
import gc
import hardware
import network
import mylib
from Configurations import Configurations

configs = Configurations("main")
wlan = network.WLAN(network.WLAN.IF_STA)

ntptime.settime()
UTC_OFFSET = -3 * 3600  # -3 horas en segundos
print('Iniciando bot')
bot = utelegram.ubot(configs.debug)
print(f'Estado de debug: {configs.debug}')

releDif = hardware.releDif() # relé utilizado para hacer saltar al diferencial
releContac = hardware.releContac() # relé utilizado para accionar el contactor de 220V
sensor_st = hardware.sensor()  # sensor del estudio

while True:
    try:
        if wlan.isconnected():
            
            if bot.commands is None:
                bot.getCommands()
                print(f'Lista de comandos: {bot.commands}')
            else:
                if bot.message_offset is None:
                    bot.get_msg_id()

                if not bot.greeting:
                    bot.saluda()
                    bot.greeting = True
                
                print('bot en escucha')
                if bot.read_once():

                    # Analiza el comando recibido y responde
                    if bot.command == '/ping':
                        bot.reply_ping(bot.chat_id)

                    elif bot.command == '/estado':
                        msg = ""
                        # Obtiene los valores de temperatura y humedad del sensor cableado (estudio)
                        if sensor_st.update_values():
                            msg = f"Temperatura: {sensor_st.get_temp()}° \nHumedad: {sensor_st.get_hum()}%\n"
                            #bot.send(bot.chat_id, f'Temperatura: {sensor_st.get_temp()}° - Humedad: {sensor_st.get_hum()}%')
                        else:
                            msg = 'No puedo obtener los datos del sensor\n'
                            #bot.send(bot.chat_id, 'No puedo obtener los datos del sensor')
                        # Estado de la red de 220V
                        estado_rele = releContac.status()
                        print(f'estado: {estado_rele}')
                        if not estado_rele:
                            status = "Desconectado"
                        else:
                            status = "Conectado"
                        msg = msg + "Suministro: " + status + '\n'
                        msg = msg + mylib.formatTime(time, UTC_OFFSET)
                        #bot.send(bot.chat_id, f'Suministro 220V: {status}')
                        if not bot.send(bot.chat_id, msg):
                            print("Timeout de respuesta a estado")
                            print("Desconectando wifi")
                            wlan.disconnect()
                        
                    elif bot.command == '/cortar':
                        # se activa relé que pone a tierra el vivo de la red de 220V.
                        print('Ejecutando apagado de emergencia')
                        bot.send(bot.chat_id, "Ok, vamos a cortar la energía")
                        if releDif.shutdown():
                            bot.send(bot.chat_id, "Se ha cortado la energía")
                        else:
                            bot.send(bot.chat_id, "Parece que no lo he logrado")

                    elif bot.command == "/apagar":
                        #Acciona contactor que releva la red de 220V
                        print("Apagando la radio")
                        if releContac.status():
                            bot.send(bot.chat_id, "Apagando la radio")
                            releContac.off()
                            time.sleep(0.5)
                            if not releContac.status():
                                msg = "Se ha apagado la radio"
                                #bot.send(bot.chat_id, "Se ha apagado la radio")
                            else:
                                msg = "Parece que no lo he logrado"
                                #bot.send(bot.chat_id, "Parece que no lo he logrado")

                            if not bot.send(bot.chat_id, msg):
                                print("Timeout de respuesta a apagar")
                                print("Desconectando wifi")
                                wlan.disconect()
                                
                        else:
                            bot.send(bot.chat_id, "Ya está apagada")

 
                    elif bot.command == "/encender":
                        #Acciona contactor que conecta la red de 220V
                        print("Encendiendo la radio")
                        if not releContac.status():
                            bot.send(bot.chat_id, "Encendiendo la radio")
                            releContac.on()
                            time.sleep(0.5)
                            if releContac.status():
                                msg = "Se ha encendido la radio"
                                #bot.send(bot.chat_id, "Se ha encendido la radio")
                            else:
                                msg = "Parece que no lo he logrado"
                                #bot.send(bot.chat_id, "Parece que no lo he logrado")
                            
                            if not bot.send(bot.chat_id, msg):
                                print("Timeout de respuesta a encender")
                                print ("Desconectando wifi")
                                wlan.disconect()

                        else:
                            bot.send(bot.chat_id, "Ya está encendida")



                    elif bot.command == '/reset':
                        print('Reinicio de dispositivo')
                        delay = configs.reset_delay
                        bot.send(bot.chat_id, f'Ok, voy a reiniciarme en {delay} segundos.')
                        time.sleep(delay)
                        reset()
        else:
            print('Sin internet, reconectando')
            
            while not wlan.isconnected():
                wlan.connect(configs.wifi_ssid, configs.wifi_password)
                if wlan.isconnected():
                    print(f'Se ha recuperado la conexion: {wlan.ipconfig("addr4")}')
                else:
                    time.sleep(5)


    except Exception as e:
        print('Error en loop principal:', e)
        gc.collect()
        time.sleep(3)

    print('Limpiando memoria')
    time.sleep(3)
    gc.collect()
    print(f'Memoria: {gc.mem_free()}')


