from machine import reset
import utelegram
import time
import gc
import hardware
import network
from Configurations import Configurations

configs = Configurations("main")
wlan = network.WLAN(network.WLAN.IF_STA)

print('Iniciando bot')
bot = utelegram.ubot(configs.debug)
print(f'Estado de debug: {configs.debug}')

releDif = hardware.releDif() # relé utilizado para hacer saltar al diferencial
releContac = hardware.releContac() # relé utilizado para accionar el contactor de 220V
sensor_st = hardware.sensor()  # sensor del estudio

while True:
    if wlan.isconnected():
        
        if bot.commands == None:
            bot.getCommands()
            print(f'Lista de comandos: {bot.commands}')
        else:
            if not bot.greeting:
                bot.saluda()
                bot.greeting = True
                    
            print('bot en escucha')
            if bot.read_once():

                 # Analiza el comando recibido y responde
                if bot.command == '/ping':
                    bot.reply_ping(bot.chat_id)

                elif bot.command == '/estado':
                    # Obtiene los valores de temperatura y humedad del sensor cableado (estudio)
                    if sensor_st.update_values():
                        bot.send(bot.chat_id, f'Temperatura: {sensor_st.get_temp()}° - Humedad: {sensor_st.get_hum()}%')
                    else:
                        bot.send(bot.chat_id, 'No puedo obtener los datos del sensor')
                    # Estado de la red de 220V
                    print(f'estado: {releContac.status()}')
                    if not releContac.status():
                        status = "Energia desconectada"
                    elif releContac.status():
                        status = "Energía conectada"
                    
                    bot.send(bot.chat_id, f'Estado de la red de 220V: {status}')
                    
                    
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
                            bot.send(bot.chat_id, "Se ha apagado la radio")
                        else:
                            bot.send(bot.chat_id, "Parece que no lo he logrado")

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
                            bot.send(bot.chat_id, "Se ha encendido la radio")
                        else:
                            bot.send(bot.chat_id, "Parece que no lo he logrado")

                    else:
                        bot.send(bot.chat_id, "Ya está encendida")



                elif bot.command == '/reset':
                    print('Reinicio de dispositivo')
                    delay = configs.reset_delay
                    bot.send(bot.chat_id, f'Ok, voy a reiniciarme en {delay} segundos.')
                    time.sleep(delay)
                    reset()
    else:
        print('Sin internet')

    print('Limpiando memoria')
    time.sleep(3)
    gc.collect()
    print(f'Memoria: {gc.mem_free()}')
