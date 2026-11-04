import subprocess
import paho.mqtt.client as mqtt

import time

class Mqtt_listener:
    def __init__(
        self,
        broker="localhost",
        client_id="pc-auto",
        topic_cmd="pc/pc-auto/cmd",
        topic_status="pc/pc-auto/status",
        topic_resp="pc/pc-auto/resp",
        port=1883,
        keepalive=60,):
        
        self.broker = broker
        self.client_id = client_id
        self.topic_cmd = topic_cmd
        self.topic_status = topic_status
        self.topic_resp = topic_resp
        self.port = port
        self.keepalive = keepalive

        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.will_set(self.topic_status, "offline", retain=True)

        
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(self.topic_cmd)
            client.publish(self.topic_status, "pc online", retain=True)
        else:
            print("Error de conexión MQTT:", rc)


    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode().strip()

        if payload == "shutdown":
            client.publish(self.topic_resp, "apagando", retain=False)
            time.sleep(5)
            try:
                subprocess.run(
                    ["/usr/sbin/shutdown", "-h", "now"],
                    check=True
                )
            except subprocess.CalledProcessError as e:
                print("Error ejecutando apagado:", repr(e))
        
        elif payload == "ping":
            client.publish(self.topic_resp, "pong", retain=False)
        elif payload == "status":
            client.publish(self.topic_resp, "encendida", retain=False)
            

    def start(self):
        self.client.connect(self.broker, self.port, self.keepalive)
        self.client.loop_forever()
