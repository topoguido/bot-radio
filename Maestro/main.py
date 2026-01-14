from machine import reset
import utelegram
import time
import gc
import hardware
import network
from mqtt_manager import MqttManager
from Configurations import Configurations

configs = Configurations("main")
wlan = network.WLAN(network.WLAN.IF_STA)

print('Iniciando bot')
bot = utelegram.ubot(configs.debug)
print(f'Estado de debug: {configs.debug}')

releDif = hardware.releDif() # relé utilizado para hacer saltar al diferencial
releContac = hardware.releContac() # relé utilizado para accionar el contactor de 220V
sensor_st = hardware.sensor()  # sensor del estudio

mqtt = MqttManager(
    client_id=configs.client_id,
    server=configs.server,
    port=configs.port,
    topic_cmd=configs.topic_cmd,
    topic_status=configs.topic_status,
    topic_resp=configs.topic_resp
)

if wlan.isconnected():
    try:
        if mqtt.connect():
            print("MQTT conectado")
        else:
            print("MQTT sin conexion")
    except Exception as e:
       print("Error MQTT:", repr(e))

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

                #----------------------------------------------------------------------
                 # Analiza el comando recibido y responde
                if bot.command == '/ping':
                    
#                     resp = mqtt.request(b"ping", timeout_ms=5000)
#                     print(f'Respuesta de la computadora: {resp}')
#                     if resp == "pong":
#                         bot.send(bot.chat_id, "Computadora activa")        
#                     else:
#                         bot.send(bot.chat_id, "Computadora sin respuesta")        
                    bot.reply_ping(bot.chat_id)

                elif bot.command == '/estado':
                    # Obtiene los valores de temperatura y humedad del sensor cableado (estudio)
                    if sensor_st.update_values():
                        bot.send(bot.chat_id, f'Temperatura: {sensor_st.get_temp()}° - Humedad: {sensor_st.get_hum()}%')
                    else:
                        bot.send(bot.chat_id, 'No puedo obtener los datos del sensor')
                    
                    # Estado de la red de 220V
                    if configs.debug: print(f'estado del relé: {releContac.status()}')
                    if not releContac.status():
                        status = "Energia desconectada"
                    elif releContac.status():
                        status = "Energía conectada"
                    
                    bot.send(bot.chat_id, f'Estado de la red de 220V: {status}')
                    
                    # estado de la computadora
                    resp = mqtt.request(b"status", timeout_ms=5000)
                    if configs.debug: print(f'Respuesta de la computadora: {resp}')
                    if resp == "encendida":
                        # La computadora está encendida
                        bot.send(bot.chat_id, "La computadora está encendida")
                    else:
                        bot.send(bot.chat_id, "La computadora está apagada")
                    
                #----------------------------------------------------------------------                    
                elif bot.command == '/cortar':
                    # se notifica a la pc que tiene que apagar
                    resp = mqtt.request(b"shutdown", timeout_ms=5000)
                    if configs.debug: print(f'Respuesta de la computadora: {resp}')
                    if not mqtt.pc_online:
                        bot.send(bot.chat_id, "La computadora se está apagando. Se espera 10 segundos")        
                        time.sleep(10)
                    else:
                        bot.send(bot.chat_id, "No hay respuesta de la computadora")        
                        time.sleep(1)
                    # se activa relé que pone a tierra el vivo de la red de 220V.
                    print('Ejecutando apagado de emergencia')
                    bot.send(bot.chat_id, "Ok, vamos a cortar la energía")
                    if releDif.shutdown():
                        bot.send(bot.chat_id, "Se ha cortado la energía")
                    else:
                        bot.send(bot.chat_id, "Parece que no lo he logrado")

                #----------------------------------------------------------------------
                elif bot.command == "/apagar":

                    # se notifica a la pc que tiene que apagar
                    resp = mqtt.request(b"shutdown", timeout_ms=5000)
                    if configs.debug: print(f'Respuesta de la computadora: {resp}')
                    if resp == "apagando":
                        bot.send(bot.chat_id, "La computadora se está apagando. Se espera 10 segundos")        
                        time.sleep(10)
                    else:
                        bot.send(bot.chat_id, "No hay respuesta de la computadora")  
                        time.sleep(1)


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

                #----------------------------------------------------------------------   
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

                #----------------------------------------------------------------------
                elif bot.command == '/reset':
                    print('Reinicio de dispositivo')
                    delay = configs.reset_delay
                    bot.send(bot.chat_id, f'Ok, voy a reiniciarme en {delay} segundos.')
                    time.sleep(delay)
                    reset()
 
    else:
        print('Sin internet')
    time.sleep(3)
    gc.collect()

