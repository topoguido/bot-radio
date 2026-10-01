import time
import socket
from umqtt.simple import MQTTClient

class MqttManager:

    def __init__(self, client_id, server, port,
                 topic_cmd, topic_status, topic_resp):

        self.client_id = client_id
        self.server = server
        self.port = port

        self.topic_cmd = topic_cmd
        self.topic_status = topic_status
        self.topic_resp = topic_resp

        self.client = MQTTClient(
            client_id=self.client_id,
            server=self.server,
            port=self.port
        )

        self.response_received = False
        self.response_payload = None
        self.pc_online = False
        self.connected = False
        self.last_status = None


        self.client.set_callback(self._on_message)
        
        self.pc_online = False

    # -------------------------------------------------

    def _on_message(self, topic, msg):
        payload = msg.decode().strip()
        print("MQTT recibido:", topic, payload)

        if topic == self.topic_status:
            self.last_status = payload
            if payload == "pc online":
                self.pc_online = True
  
            elif payload == "offline":
                self.pc_online = False
            elif payload == "pong":
                self.response_payload = payload
                self.response_received = True
            elif payload == "apagando":
                self.response_payload = payload
                self.response_received = True
                self.pc_online = False


        elif topic == self.topic_resp:
            self.response_payload = payload
            self.response_received = True


    # -------------------------------------------------

    def broker_available(self, timeout_s=1):
        sock = None

        try:
            address = socket.getaddrinfo(
                self.server,
                self.port
            )[0][-1]

            sock = socket.socket()
            sock.settimeout(timeout_s)
            sock.connect(address)
            return True

        except OSError:
            return False

        finally:
            if sock is not None:
                sock.close()

    # -------------------------------------------------

    def connect(self):
        self.connected = False
        self.pc_online = False

        if not self.broker_available(timeout_s=1):
            print("Broker MQTT no disponible")
            return False

        try:
            self.client.connect()
            self.client.subscribe(self.topic_resp)
            self.client.subscribe(self.topic_status)
            self.connected = True
            self.flush(duration_ms=500)
            print("MQTT conectado")
            return True
        except Exception as e:
            self.connected = False
            self.pc_online = False
            print("Error conectando MQTT:", repr(e))

            return False

    # -------------------------------------------------

    def flush(self, duration_ms=300):
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < duration_ms:
            self.client.check_msg()
            time.sleep_ms(20)

    # -------------------------------------------------
    def request(self, payload, timeout_ms=5000):
        if not self.connected:
            return None

       

        # limpiar mensajes viejos
        self.flush()
         # Limpia cualquier respuesta anterior.
        self.response_received = False
        self.response_payload = None
        time.sleep(1)
        try:
            self.client.publish(self.topic_cmd, payload, retain=False)

            start = time.ticks_ms()

            while not self.response_received:
                self.client.check_msg()
                if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                    return None
                time.sleep_ms(100)

            return self.response_payload
        except Exception as e:
            self.connected = False
            self.pc_online = False
            print("Error en peticion MQTT:", repr(e))
            return None


    # -------------------------------------------------

    def loop(self):
        if not self.connected:
            return False

        try:
            self.client.check_msg()
            return True

        except Exception as e:
            self.connected = False
            self.pc_online = False
            print("Error procesando MQTT:", repr(e))
            return False
