import time
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

        self.client.set_callback(self._on_message)
        
        self.pc_online = False

    # -------------------------------------------------

    def _on_message(self, topic, msg):
        payload = msg.decode()
        if topic == self.topic_status:
            self.last_status = payload
            if payload == "pc online":
                self.pc_online = True
  
            elif payload == "offline":
                self.pc_online = False

        elif topic == self.topic_resp:
            if payload == "encendida":
                self.response_payload = payload
                self.response_received = True
            else:
                self.response_received = False

    # -------------------------------------------------

    def connect(self):
        try:
            self.client.connect()
            self.client.subscribe(self.topic_resp)
            self.client.subscribe(self.topic_status)
            return True
        except:
            return False

    # -------------------------------------------------

    def flush(self, duration_ms=300):
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < duration_ms:
            self.client.check_msg()
            time.sleep_ms(20)

    # -------------------------------------------------
    def request(self, payload, timeout_ms=5000):
        self.response_received = False
        self.response_payload = None

        # limpiar mensajes viejos
        #self.client.check_msg()
        self.flush()
        time.sleep(1)

        self.client.publish(self.topic_cmd, payload, retain=False)

        start = time.ticks_ms()

        while not self.response_received:
            self.client.check_msg()
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                return None
            time.sleep_ms(100)

        return self.response_payload

    # -------------------------------------------------

    def loop(self):
        """Para procesar mensajes asincrónicos si hiciera falta"""
        self.client.check_msg()
