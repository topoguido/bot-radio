from machine import reset
import mylib
import time, ntptime, gc, network

from Configurations import Configurations

configs = Configurations("main")
mylib.configure_output(configs.debug)
wlan = network.WLAN(network.WLAN.IF_STA)

if configs.mqtt_enabled:
    from mqtt_manager import MqttManager
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
BATTERY_LOG_INTERVAL_MS = 60 * 60 * 1000
last_battery_check = None
last_battery_log = None

MQTT_RETRY_INTERVAL_MS = 30 * 1000
last_mqtt_retry = None

ntp_warning_logged = False


mylib.log_print('Iniciando bot')

import utelegram, hardware

bot = utelegram.ubot(configs.debug)
mylib.log_print(f'Estado de debug: {configs.debug}')

mylib.log_print("Rele diferencial")
releDif = hardware.releDif(configs.relayDif_Pin) # relé utilizado para hacer saltar al diferencial
mylib.log_print("Rele contactor")
releContac = hardware.releContac(configs.relayContact_Pin) # relé utilizado para accionar el contactor de 220V
mylib.log_print("Sensor temperatura")
sensor_st = hardware.sensor(configs.sensorTH_Pin)  # sensor del estudio
mylib.log_print("Sensor AC")
AC_sensor = hardware.ACSensor(configs.sensorAC_IN_Pin, configs.sensorAC_OUT_Pin) #sensores de tension AC aguas arriba y abajo del relé principal
mylib.log_print("Sensor DC")
DC_sensor = hardware.DCSensor(configs.sensorDC_Pin) # sensor de tension DC de la bateria
mylib.log_print("Rele cargador")
cargadorBat = hardware.releCarga(configs.batt_Vmin,
                                 configs.batt_Vmax,
                                 configs.debug,
                                 configs.relayCharger_Pin) # Relé que activa el cargador de bateria

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
                try:
                    ntptime.host = "pool.ntp.org"
                    ntptime.settime()
                    time_flag = True
                    ntp_recovered = ntp_warning_logged
                    ntp_warning_logged = False
                    mylib.log_print("Sistema iniciado")
                    if ntp_recovered:
                        mylib.log_print("Servicio NTP recuperado")
                    else:
                        mylib.log_print("Hora sincronizada por NTP")
                except OSError as e:
                    if not ntp_warning_logged:
                        mylib.log_print(
                            "No se pudo sincronizar NTP:",
                            repr(e),
                            level=mylib.WARNING,
                            exception=e,
                        )
                        ntp_warning_logged = True
            gc.collect()
            if bot.commands is None:
                commands = bot.getCommands()
                if commands is not None:
                    mylib.log_print(f'Lista de comandos: {commands}')
            else:
                if bot.message_offset is None:
                    bot.get_msg_id()

                if not bot.greeting:
                    bot.greeting = bot.saluda()
                    if not bot.greeting:
                        time.sleep(3)
                        continue

                now = time.ticks_ms()

                if ( last_battery_check is None
                    or time.ticks_diff(now, last_battery_check) >= BATTERY_CHECK_INTERVAL_MS ):
                    Vbat = DC_sensor.getStatus()
                    if (
                        last_battery_log is None
                        or time.ticks_diff(now, last_battery_log)
                            >= BATTERY_LOG_INTERVAL_MS
                    ):
                        mylib.log_print(f"Tension de bateria: {Vbat} V")
                        last_battery_log = now

                    if configs.charger_enabled:
                        previous_charger_status = cargadorBat.status()
                        charger_status = cargadorBat.checkCarga(Vbat)
                        if charger_status is not None and charger_status != previous_charger_status:
                            mylib.log_print(
                                "Cargador de bateria {} con tension {:.2f} V".format(
                                    "encendido" if charger_status else "apagado",
                                    Vbat,
                                )
                            )
                        last_battery_check = now
                
                message_received = bot.read_once()
                if bot.get_updates_failures >= 3:
                    mylib.log_print(
                        "Tres fallos consecutivos de Telegram; reconectando Wi-Fi",
                        level=mylib.WARNING,
                    )
                    bot.get_updates_failures = 0
                    wlan.disconnect()
                    time.sleep(1)
                    continue

                if message_received:

                    # Analiza el comando recibido y responde
                    if bot.command == '/ping':
                        if bot.reply_ping(bot.chat_id):
                            mylib.log_print("Respuesta al comando /ping enviada")
                        # estado de la computadora
                        mylib.log_print(
                            f"configs.mqtt_enabled: {configs.mqtt_enabled}",
                            level=mylib.DEBUG,
                        )

                        if configs.mqtt_enabled:
                            if mqtt.pc_online:
                                mylib.log_print(
                                    f"mqtt.pc_online: {mqtt.pc_online}",
                                    level=mylib.DEBUG,
                                )
                                resp = mqtt.request(b"ping", timeout_ms=5000)
                                mylib.log_print(
                                    f'Respuesta de la computadora: {resp}',
                                    level=mylib.DEBUG,
                                )
                                if resp == "pong":
                                    pc_status = "Encendida"
                                else:
                                    pc_status = "Sin respuesta"
                                bot.send(bot.chat_id, "Computadora: " + pc_status)

                    elif bot.command == '/estado':
                        msg = ""
                        # Obtiene los valores de temperatura y humedad del sensor cableado (estudio)
                        if sensor_st.update_values():
                            msg = f"Temperatura: {sensor_st.get_temp()}° - Humedad: {sensor_st.get_hum()}%\n"
                            mylib.log_print(
                                f"Temperatura: {sensor_st.get_temp()}°",
                                level=mylib.DEBUG,
                            )
                        else:
                            msg = 'No puedo obtener los datos del sensor\n'
                        
                        # Estado de la red de 220V
                        tension_AC_In, hayTension_AC_In = AC_sensor.getStatusAC_In()
                        tension_AC_Out, hayTension_AC_Out = AC_sensor.getStatusAC_Out()

                        mylib.log_print(
                            f"estado: AC In: {tension_AC_In:.0f} V - "
                            f"AC Out: {tension_AC_Out:.0f} V",
                            level=mylib.DEBUG,
                        )

                        
                        if hayTension_AC_In:
                            rele_in_status = "Conectado"
                        else:
                            rele_in_status = "Desconectado"

                        mylib.log_print(
                            f"Energía pilar: {rele_in_status}",
                            level=mylib.DEBUG,
                        )

                        if hayTension_AC_Out:
                            rele_out_status = "Conectado"
                        else:
                            rele_out_status = "Desconectado" 

                        mylib.log_print(
                            "Energía interna: " + rele_out_status,
                            level=mylib.DEBUG,
                        )

                        msg = msg + "Suministro pilar: " + rele_in_status + '\n'
                        msg = msg + "Suministro interno: " + rele_out_status + '\n'
                        msg += "Tensión AC: {:.1f} V\n".format(tension_AC_Out)
                        msg += "Tensión batería: {:.1f} V\n".format(DC_sensor.getStatus())
                        
                        # Estado de la bateria
                        if configs.charger_enabled:
                            msg += "Cargador bateria: " + {0: "Apagado", 1: "Encendido"}.get(cargadorBat.status(), "Estado desconocido") + "\n"
                        else:
                            msg += "Cargador bateria: Deshabilitado\n"
                        
                        # estado de la computadora
                        if configs.mqtt_enabled:
                            resp = mqtt.request(b"status", timeout_ms=5000)
                            mylib.log_print(
                                f'Respuesta de la computadora: {resp}',
                                level=mylib.DEBUG,
                            )
                            if resp == "encendida":
                                pc_status = "Encendida"
                            else:
                                pc_status = "Apagada"
                            msg = msg + "Computadora: " + pc_status + '\n'
                        msg = msg + mylib.formatTime(time, UTC_OFFSET)

                        if not bot.send(bot.chat_id, msg):
                            mylib.log_print(
                                "Error de respuesta al comando estado",
                                level=mylib.ERROR,
                            )
                        else:
                            mylib.log_print(f"Respuesta al comando /estado: {msg}", level=mylib.DEBUG)
                        
                    elif bot.command == '/cortar':
                        # se activa relé que pone a tierra el vivo de la red de 220V.
                        mylib.log_print(
                            'Ejecutando apagado de emergencia',
                            level=mylib.WARNING,
                        )
                        bot.send(bot.chat_id, "Ok, vamos a cortar la energía")
                        if configs.mqtt_enabled and mqtt.pc_online:
                            resp = mqtt.request(b"shutdown", timeout_ms=5000)
                            mylib.log_print(
                                f'Respuesta de la computadora: {resp}',
                                level=mylib.DEBUG,
                            )
                            if resp == "apagando":
                                bot.send(bot.chat_id, "La computadora se está apagando. Se espera 10 segundos")
                                time.sleep(15)
                            else:
                                bot.send(bot.chat_id, "No hay respuesta de la computadora")
                                time.sleep(1)

                        if releDif.shutdown():
                            mylib.log_print("Se corto la energia mediante el rele diferencial")
                            bot.send(bot.chat_id, "Se ha cortado la energía")
                        else:
                            mylib.log_print(
                                "No se pudo accionar el rele diferencial",
                                level=mylib.ERROR,
                            )
                            bot.send(bot.chat_id, "No he logrado cortar la energia")

                    elif bot.command == "/apagar":
                        #Acciona contactor que releva la red de 220V
                        mylib.log_print("Solicitud para apagar la radio")

                        # se notifica a la pc que tiene que apagar
                        if configs.mqtt_enabled and mqtt.pc_online:
                            resp = mqtt.request(b"shutdown", timeout_ms=5000)
                            mylib.log_print(
                                f'Respuesta de la computadora: {resp}',
                                level=mylib.DEBUG,
                            )
                            if resp == "apagando":
                                bot.send(bot.chat_id, "La computadora se está apagando. Se espera 10 segundos")        
                                time.sleep(15)

                        mylib.log_print("Consultando datos AC", level=mylib.DEBUG)
                        _, AC_in_status = AC_sensor.getStatusAC_In()
                        _, AC_out_status = AC_sensor.getStatusAC_Out()
                        
                        
                        if AC_in_status and AC_out_status:
                            # Se detecta tension arriba y abajo del relé.
                            bot.send(bot.chat_id, "Apagando la radio")
                            releContac.changeStatus()

                            mylib.log_print(
                                "Consultando sensor salida AC",
                                level=mylib.DEBUG,
                            )
                            _, AC_out_status = AC_sensor.getStatusAC_Out()
                            mylib.log_print(
                                f"Respuesta sensor: {AC_out_status}",
                                level=mylib.DEBUG,
                            )
                            if not AC_out_status:
                                msg = "Se ha apagado la radio"
                                mylib.log_print("Radio apagada")
                                bot.send(bot.chat_id, msg)
                            else:
                                msg = "No he logrado apagar la radio"
                                mylib.log_print(
                                    "No se pudo apagar la radio",
                                    level=mylib.ERROR,
                                )
                                bot.send(bot.chat_id, msg)

                                
                        elif AC_in_status and not AC_out_status:
                            mylib.log_print("La radio ya estaba apagada")
                            bot.send(bot.chat_id, "Ya está apagada")

 
                    elif bot.command == "/encender":
                        #Acciona contactor que conecta la red de 220V
                        _, AC_in_status = AC_sensor.getStatusAC_In()
                        _, AC_out_status = AC_sensor.getStatusAC_Out()
                        mylib.log_print("Solicitud para encender la radio")
                        if not AC_out_status:
                            bot.send(bot.chat_id, "Encendiendo la radio")
                            releContac.changeStatus()
                            time.sleep(0.5)
                            _, AC_out_status = AC_sensor.getStatusAC_Out()
                            if AC_out_status:
                                msg = "Se ha encendido la radio"
                                mylib.log_print("Radio encendida")
                                bot.send(bot.chat_id, msg)
                            else:
                                msg = "Parece que no lo he logrado"
                                mylib.log_print(
                                    "No se pudo encender la radio",
                                    level=mylib.ERROR,
                                )
                                bot.send(bot.chat_id, "Parece que no lo he logrado")


                        elif AC_in_status and AC_out_status:
                            mylib.log_print("La radio ya estaba encendida")
                            bot.send(bot.chat_id, "Ya está encendida")



                    elif bot.command == '/reset':
                        mylib.log_print(
                            'Reinicio de dispositivo solicitado',
                            level=mylib.WARNING,
                        )
                        delay = configs.reset_delay
                        bot.send(bot.chat_id, f'Ok, voy a reiniciarme en {delay} segundos.')
                        time.sleep(delay)
                        reset()
        else:
            mylib.log_print('Sin internet, reconectando', level=mylib.WARNING)
            
            while not wlan.isconnected():
                wlan.connect(configs.wifi_ssid, configs.wifi_password)
                if wlan.isconnected():
                    mylib.log_print(
                        f'Se ha recuperado la conexion: {wlan.ipconfig("addr4")}'
                    )
                else:
                    time.sleep(5)
    
        time.sleep(3)
        gc.collect()
        t = time.localtime(time.time() + UTC_OFFSET)
        if t[4] == 0 and t[5] < 10 and check_internet_flag:
            check_internet_flag = False
            if not bot.test_connection():
                mylib.log_print("Check de internet: Error", level=mylib.WARNING)
                wlan.disconnect()

        elif t[4] != 0:
            check_internet_flag = True
    
    except Exception as e:
        mylib.log_print(
            'Error en loop principal:',
            e,
            level=mylib.ERROR,
            exception=e,
        )
        gc.collect()
        time.sleep(3)

    
