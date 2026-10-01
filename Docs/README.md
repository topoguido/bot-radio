# bot-radio
Bot para ejecutar acciones en la radio

### Carpeta Maestro:

Dispositivo ESP32 que aloja el bot de Telegram. 
Al iniciar, ejecuta OTA para verificar actualizaciones. Luego solicita a la API de Telegram los comandos asignados para ese bot.
Luego se mantiene en escucha (haciendo request a API de Telegram) esperando nuevos mensajes. Solo reconocerá los comandos asignados al bot.
Tambien cada cierto tiempo analiza la tensión de la bateria.

### Comandos:

/saluda: captura el nombre de la cuenta que le envía el comando y responde con un saludo.

/ping: responde con el texto "pong"

/apagar:  acciona el relé conectado al pin 3 durante 0.5 segundos. Este relé unirá el vivo de la instalación de 220V con la tierra. De esta manera se hace saltar al disyuntor diferencial desvinculando la instalacion interna de la linea que viene de la calle.

/reset: reinicia el dispositivo con un delay determina en el archivo config.py.

/cortar: opera un relé que pone a tierra el vivo de la instalación de 220V de manera de relevar el disyuntor diferencial.

/estado: toma los valores del DHT11, de los sensores de corriente alterna y el sensor de corriente contínua que corresponde a la batería. Responde al chat con los datos tomados. 

Este dispositivo contiene el archivo temp.json que no existe en el repositorio. Este archivo contiene la clave 
msg = { 'ultimo_id_msg': 941431892 } que es utilizada por el metodo que recibe los mensajes para guardar el ultimo id. De esta forma solo se tomarian mensajes con id superiores. Al llegar un mensaje, se actualiza este id. 
Si no encuentra el archivo, lo crea con id = 1. Al recibir un mensaje lo actualiza.

--------------------------------------------------------------------------------
## Configuraciones:

archivo: bot_config.json
estructura:

{
    "token": "",
    "chat_id_default": ""
    "group_id_default": ""
}

token = token del bot provisto por telegram
chat_id_default = Es el id del chat con el cual se quiere operar el bot
group_id_default = Idem, pero de grupos. En caso de que quiera agregarse al bot a un grupo.

Una manera de obtener los id es hacer pruebas haciendo un post a la api de telegram con postman por ejemplo. Ver la doc de telegram acerca de como hacer un request.

archivo: config.json
estructura:
{
  "wifi_config": {
    "ssid": "",
    "password": ""
  },

  "device_conf": {
    "reset_delay": 5
  },

  "update_params": {
    "status": false,
    "user": "topoguido",
    "repo": "bot-radio",
    "branch": "main",
    "files": ["boot.py", "main.py", "hardware.py", "utelegram.py", "Bot_configurations.py", 
              "Configurations.py", "config.json", "mylib.py", "mqtt_manager.py"],
    "working_dir": "Maestro"
  },

  "mqtt_conf": {
    "enabled": false,
    "server": "192.168.2.108",
    "port": 1883,
    "client_id": "esp32",
    "topic_cmd": "pc/pc-auto/cmd",
    "topic_status": "pc/pc-auto/status",
    "topic_resp": "pc/pc-auto/resp"
  },

  "batt_conf":{
    "Vmin": 11.4,
    "Vmax": 14.3
  },

  "debug": true
}
--------------------------------------------------------------------------------


## Conexiones

Pin 1: Datos del sensor de DC. (tension contínua de la batería)
Pin 2: Accionamiento del relé que alimenta al cargador de la batería.
Pin 3: Lector del sensor AC conectado aguas arriba del relé que alimenta contactor principal. Se conecta por medio de un divisor resistivo (ver circuito 1)
Pin 4: Lector del sensor AC conectado aguas abajo del relé del contactor. Se conecta por medio de un divisor resistivo (ver circuito 2)
Pin 5: Conectado a circuito de accionamiento del relé que alimenta contactor principal (ver circuito 3)
Pin 6: Lectura de datos del sensor DHT11.
Pin 7: Accionamiento del relé que pone el vivo de la instalación eléctrica, a tierra. De esta forma fuerza al disyuntor diferencial a accionarse y relevar toda la instalación del servicio eléctrico.

--------------------------------------------------------------------------------
## Control de carga de la bateria

Para utilizar un cargador común de 12V y 10A controlado por tu propio circuito de voltaje, debes emular de forma automática los límites de seguridad que haría un cargador inteligente. Al tener una corriente fija de 10A (que está perfectamente dentro del límite saludable de 30A para esta batería), tu circuito debe cortar y encender el cargador en los siguientes puntos exactos:
Umbrales de Configuración para tu Circuito
• Voltaje de APAGADO (Corte de carga): 14.4 V
	• Por qué: Al ser una batería de GEL, es sumamente sensible a la sobrecarga. Si dejas que el cargador común supere los 14.4 V, el gel comenzará a gasificar y perderá agua (se secará), destruyendo la batería de forma irreversible ya que es sellada. Cortar estrictamente a los 14.4 V protegerá su vida útil.
• Voltaje de ENCENDIDO (Reconexión): 12.2 V
	• Por qué: Este valor corresponde aproximadamente al 50% de la capacidad de la batería en reposo. Evitar que caiga por debajo de este punto garantizará que la batería te dure muchos años (más de 1,000 ciclos de uso).
Consideración Crítica: El "Efecto Rebote"
Cuando tu circuito esté midiendo el voltaje, debes programar una lógica o histéresis para evitar que el cargador se encienda y apague como un "parpadeo" constante:
1. Durante la carga: El cargador inyectará 10A, lo que hará que el voltaje medido suba artificialmente rápido. Tu circuito leerá 14.4 V y apagará el cargador.
2. Al apagar el cargador: El voltaje de la batería caerá instantáneamente unas décimas de voltio (por ejemplo, a 13.2 V o 13.5 V) porque ya no recibe la corriente del cargador. Esto es normal.
3. La regla: Tu circuito no debe volver a encender el cargador inmediatamente cuando el voltaje baje de 14.4 V. Solo debe encenderlo cuando la batería se haya descargado por el uso real del sistema hasta llegar a los 12.2 V.
--------------------------------------------------------------------------------
## Sensores de corriente alterna:

Estos sensores van conectados a los circuitos 1 y 2. Los circuitos son divisores resistivos que no es obligatorio sean estos valores (son las resistencias que yo tenia en su momento). Pueden variarse los valores, pero hay que recalcular los valores de RMS. El ejemplo puede verse en Docs/test_rele.py. Se debe lograr una calibracion midiendo con multimetro la tension AC y viendo que arroja por consola el ESP32.

Circuito 1 (sensor arriba del relé principal)

![](https://github.com/topoguido/bot-radio/blob/f8c10bb764e7a39946acb62062fb5c83bc03ccaa/Docs/Circuito-1.jpeg)




Circuito 2 (sensor debajo del relé principal)

![](/home/emiliano/Proyectos/ESPduino/bot-radio/Docs/Circuito-2.jpeg)

Accionamiento del relé principal (contactor)
Este relé es como un bi-estable o flip-flop. A diferencia de los relés comunes que necesitan mantener en HIGH el pin de señal, estos solo necesitan un pulso corto para cambiar de estado. En mi práctica resultó mejor hacer un circuito simulando un relé electronico para accionar este relé. El objetivo fue proteger al relé de los pequeños pulsos que se puedan generar en los pines del ESP32 cuando inicia. Esto estaba generando señales falsas y cambiando de posición el relé bi-estable.

Circuito

![](/home/emiliano/Proyectos/ESPduino/bot-radio/Docs/Circuito-3.png)

Se trata de un transistor genérico (BC547, BC548, 2N3904). La base tiene conectadas dos resistencias, una de ellas de valor 4,7 KΩ va entre la base y el pin del ESP. La otra conecta la base a GND y es de valor 10 KΩ. El emisor se conecta directo al borne de señal del relé (borne negativo). El colector se conecta al otro borne del relé (borne positivo).

Repositorio de GitHub: https://github.com/topoguido/bot-radio.git



