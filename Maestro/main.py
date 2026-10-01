from machine import reset
import utelegram
import time
import ntptime
import gc
import hardware
import network
import mylib
from mqtt_manager import MqttManager
from Configurations import Configurations

configs = Configurations("main")
wlan = network.WLAN(network.WLAN.IF_STA)

mqtt = MqttManager(
    client_id=configs.client_id,
    server=configs.server,
    port=configs.port,
    topic_cmd=configs.topic_cmd,
    topic_status=configs.topic_status,
    topic_resp=configs.topic_resp
)

UTC_OFFSET = -3 * 3600  # -3 horas en segundos
check_internet_flag = True
time_flag = False

BATTERY_CHECK_INTERVAL_MS = 2 * 60 * 1000
last_battery_check = None

MQTT_RETRY_INTERVAL_MS = 30 * 1000
last_mqtt_retry = None

print('Iniciando bot')
bot = utelegram.ubot(configs.debug)
print(f'Estado de debug: {configs.debug}')

releDif = hardware.releDif() # relé utilizado para hacer saltar al diferencial
releContac = hardware.releContac() # relé utilizado para accionar el contactor de 220V
sensor_st = hardware.sensor()  # sensor del estudio
AC_sensor = hardware.ACSensor() #sensores de tension AC aguas arriba y abajo del relé principal
DC_sensor = hardware.DCSensor() # sensor de tension DC de la bateria
cargadorBat = hardware.releCarga(configs.batt_Vmin,
                                 configs.batt_Vmax, 
                                 configs.debug) # Relé que activa el cargador de bateria

while True:
    try:
        if wlan.isconnected():
            if configs.mqtt_enabled:
                if mqtt.connected:
                    mqtt.loop()
                else:
                    now = time.ticks_ms()

                    if (
                        last_mqtt_retry is None
                        or time.ticks_diff(now, last_mqtt_retry)
                            >= MQTT_RETRY_INTERVAL_MS
                    ):
                        last_mqtt_retry = now
                        mqtt.connect()
            
            if not time_flag:
                ntptime.settime()
                time_flag = True

            if bot.commands is None:
                bot.getCommands()
                print(f'Lista de comandos: {bot.commands}')
            else:
                if bot.message_offset is None:
                    bot.get_msg_id()

                if not bot.greeting:
                    bot.saluda()
                    bot.greeting = True

                now = time.ticks_ms()

                if ( last_battery_check is None
                    or time.ticks_diff(now, last_battery_check) >= BATTERY_CHECK_INTERVAL_MS ):
                    if configs.debug:
                        print("Chequeando bateria")

                    cargadorBat.checkCarga(DC_sensor.getStatus())
                    last_battery_check = now
                
                print('bot en escucha')
                if bot.read_once():

                    # Analiza el comando recibido y responde
                    if bot.command == '/ping':
                        bot.reply_ping(bot.chat_id)
                        # estado de la computadora
                        print(f"configs.mqtt_enabled: {configs.mqtt_enabled}")
                        print(f"mqtt.pc_online: {mqtt.pc_online}")
                        if configs.mqtt_enabled and mqtt.pc_online:
                            resp = mqtt.request(b"ping", timeout_ms=5000)
                            if configs.debug: print(f'Respuesta de la computadora: {resp}')
                            if resp == "pong":
                                pc_status = "Encendida"
                            else:
                                pc_status = "Sin respuesta"
                            bot.send(bot.chat_id, "Computadora: " + pc_status)

                    elif bot.command == '/estado':
                        msg = ""
                        # Obtiene los valores de temperatura y humedad del sensor cableado (estudio)
                        if sensor_st.update_values():
                            msg = f"Temperatura: {sensor_st.get_temp()}° \nHumedad: {sensor_st.get_hum()}%\n"
                            if configs.debug:
                                print(f"Temperatura: {sensor_st.get_temp()}°")
                        else:
                            msg = 'No puedo obtener los datos del sensor\n'
                        
                        # Estado de la red de 220V
                        tension_AC_In, hayTension_AC_In = AC_sensor.getStatusAC_In()
                        tension_AC_Out, hayTension_AC_Out = AC_sensor.getStatusAC_Out()

                        if configs.debug:
                            print(
                                    f"estado: AC In: {tension_AC_In:.0f} V - "
                                    f"AC Out: {tension_AC_Out:.0f} V"
                                )

                        
                        if hayTension_AC_In:
                            rele_in_status = "Conectado"
                        else:
                            rele_in_status = "Desconectado"

                        if configs.debug:
                            print(f"Energía pilar: {rele_in_status}")

                        if hayTension_AC_Out:
                            rele_out_status = "Conectado"
                        else:
                            rele_out_status = "Desconectado" 

                        if configs.debug:
                            print("Energía interna: " + rele_out_status)  

                        msg = msg + "Suministro pilar: " + rele_in_status + '\n'
                        msg = msg + "Suministro interno: " + rele_out_status + '\n'
                        msg += "Tensión AC: {:.1f} V\n".format(tension_AC_Out)
                        msg += "Tensión batería: {:.1f} V\n".format(DC_sensor.getStatus())
                        
                        # Estado de la bateria
                        msg += "Cargador bateria: " + {0: "Apagado", 1: "Encendido"}.get(cargadorBat.status(), "Estado desconocido") + "\n"
                        
                        if configs.debug:
                            print(msg)

                        # estado de la computadora
                        if configs.mqtt_enabled:
                            resp = mqtt.request(b"status", timeout_ms=5000)
                            if configs.debug: print(f'Respuesta de la computadora: {resp}')
                            if resp == "encendida":
                                pc_status = "Encendida"
                            else:
                                pc_status = "Apagada"
                            msg = msg + "Computadora: " + pc_status + '\n'
                            msg = msg + mylib.formatTime(time, UTC_OFFSET)

                        if not bot.send(bot.chat_id, msg):
                            print("Error de respuesta a estado")
                        
                    elif bot.command == '/cortar':
                        # se activa relé que pone a tierra el vivo de la red de 220V.
                        print('Ejecutando apagado de emergencia')
                        bot.send(bot.chat_id, "Ok, vamos a cortar la energía")
                        if configs.mqtt_enabled and mqtt.pc_online:
                            resp = mqtt.request(b"shutdown", timeout_ms=5000)
                            if configs.debug: print(f'Respuesta de la computadora: {resp}')
                            if resp == "apagando":
                                bot.send(bot.chat_id, "La computadora se está apagando. Se espera 10 segundos")
                                time.sleep(15)
                            else:
                                bot.send(bot.chat_id, "No hay respuesta de la computadora")
                                time.sleep(1)

                        if releDif.shutdown():
                            bot.send(bot.chat_id, "Se ha cortado la energía")
                        else:
                            bot.send(bot.chat_id, "No he logrado cortar la energia")

                    elif bot.command == "/apagar":
                        #Acciona contactor que releva la red de 220V
                        print("Apagando la radio")

                        # se notifica a la pc que tiene que apagar
                        if configs.mqtt_enabled and mqtt.pc_online:
                            resp = mqtt.request(b"shutdown", timeout_ms=5000)
                            if configs.debug: print(f'Respuesta de la computadora: {resp}')
                            if resp == "apagando":
                                bot.send(bot.chat_id, "La computadora se está apagando. Se espera 10 segundos")        
                                time.sleep(15)

                        print("Consultando datos AC")
                        _, AC_in_status = AC_sensor.getStatusAC_In()
                        _, AC_out_status = AC_sensor.getStatusAC_Out()
                        
                        
                        if AC_in_status and AC_out_status:
                            # Se detecta tension arriba y abajo del relé.
                            bot.send(bot.chat_id, "Apagando la radio")
                            releContac.changeStatus()

                            print("Consultando sensor salida AC")
                            _, AC_out_status = AC_sensor.getStatusAC_Out()
                            print(f"Respuesta sensor: {AC_out_status}")
                            if not AC_out_status:
                                msg = "Se ha apagado la radio"
                                bot.send(bot.chat_id, msg)
                            else:
                                msg = "No he logrado apagar la radio"
                                bot.send(bot.chat_id, msg)

                                
                        elif AC_in_status and not AC_out_status:
                            bot.send(bot.chat_id, "Ya está apagada")

 
                    elif bot.command == "/encender":
                        #Acciona contactor que conecta la red de 220V
                        _, AC_in_status = AC_sensor.getStatusAC_In()
                        _, AC_out_status = AC_sensor.getStatusAC_Out()
                        print("Encendiendo la radio")
                        if not AC_out_status:
                            bot.send(bot.chat_id, "Encendiendo la radio")
                            releContac.changeStatus()
                            time.sleep(0.5)
                            _, AC_out_status = AC_sensor.getStatusAC_Out()
                            if AC_out_status:
                                msg = "Se ha encendido la radio"
                                bot.send(bot.chat_id, msg)
                            else:
                                msg = "Parece que no lo he logrado"
                                bot.send(bot.chat_id, "Parece que no lo he logrado")


                        elif AC_in_status and AC_out_status:
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
    
        print('Limpiando memoria')
        time.sleep(3)
        gc.collect()
        print(f'Memoria: {gc.mem_free()}')
        t = time.localtime(time.time() + UTC_OFFSET)
        if t[4] == 0 and t[5] < 10 and check_internet_flag:
            check_internet_flag = False
            if bot.test_connection():
                print("Check de internet: OK")
                pass
            else:
                print("Check de internet: Error")
                wlan.disconnect()

        elif t[4] != 0:
            check_internet_flag = True
    
    except Exception as e:
        print('Error en loop principal:', e)
        gc.collect()
        time.sleep(3)

    
