# bot-radio
Bot para ejecutar acciones en la radio

Carpeta Esclavo: 
Código para el ESP8266
Este dispositivo mantiene dos procesos corriendo de manera asíncrona. 

Método rele_control(): Se encarga de cada 6 segundos medir la temperatura con un DHT11 (pin D1) y en caso de superar los 28°, enciende un cooler por medio del relé (pin D2).

Método msg_control(): Mantiene escucha por medio del wifi usando ESPNOW. Si recibe el mensaje con el texto "values", toma los datos del DHT11 y los envía a la MAC de broadcast ya que el receptor se mantiene conectado a un AP. 


Carpeta Maestro:
Dispositivo ESP32 que aloja el bot de Telegram. 
Al iniciar, ejecuta OTA para verificar actualizaciones. Luego solicita a la API de Telegram los comandos asignados para ese bot.
Luego se mantiene en escucha (haciendo request a API de Telegram) esperando nuevos mensajes. Solo reconocerá los comandos asignados al bot.

Comandos:
/saluda: captura el nombre de la cuenta que le envía el comando y responde con un saludo.

/ping: responde con el texto "pong"

/apagar:  acciona el relé conectado al pin 3 durante 0.5 segundos. Este relé unirá el vivo de la instalación de 220V con la tierra. De esta manera se hace saltar al disyuntor diferencial desvinculando la instalacion interna de la linea que viene de la calle.

/reset: reinicia el dispositivo con un delay determina en el archivo config.py.

/temp: toma los valores del DHT11 y responde al chat con ellos. Luego le solicita al esclavo (ESP8266) por medio de ESPNOW los valores de su DHT11. Al recibirlos, los envia en otro mensaje al chat.

Este dispositivo contiene el archivo temp.py que no existe en el repositorio. Este archivo contiene la clave 
msg = { 'ultimo_id_msg': 941431892 } que es utilizada por el metodo que recibe los mensajes para guardar el ultimo id. De esta forma solo se tomarian mensajes con id superiores. Al llegar un mensaje, se actualiza este id. 
Esta fué la solución al loop que genera cuando se le envia la orden de reiniciar. Levanta nuevamente y vuelve a recibir el mismo mensaje, volviendo a reiniciar y asi sucesivamente... 

--------------------------------------------------------------------------------
Repositorio de GitHub: https://github.com/topoguido/bot-radio.git

Rama: dev

