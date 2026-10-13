import json

class Configurations:

    def __init__(self, type):

        with open("config.json", "r") as f:
            data =  json.load(f)

            self.debug = data["debug"]
            self.logging_status = data["logging"]["enabled"]

            if type == "boot":
                self.wifi_ssid = data["wifi_config"]["ssid"]
                self.wifi_password = data["wifi_config"]["password"]
                self.update_status = data["update_params"]["status"]
                self.update_user = data["update_params"]["user"]
                self.update_repo = data["update_params"]["repo"]
                self.update_branch = data["update_params"]["branch"]
                self.update_files = data["update_params"]["files"]
                self.update_working_dir = data["update_params"]["working_dir"]

            if type == "main":
                self.reset_delay = data["device_conf"]["reset_delay"]
                self.wifi_ssid = data["wifi_config"]["ssid"]
                self.wifi_password = data["wifi_config"]["password"]

                self.mqtt_enabled = data["mqtt_conf"]["enabled"]
                self.server = data["mqtt_conf"]["server"]
                self.port = data["mqtt_conf"]["port"]
                self.client_id = data["mqtt_conf"]["client_id"].encode()
                self.topic_cmd = data["mqtt_conf"]["topic_cmd"].encode()
                self.topic_status = data["mqtt_conf"]["topic_status"].encode()
                self.topic_resp  = data["mqtt_conf"]["topic_resp"].encode()

                self.batt_Vmin = data["batt_conf"]["Vmin"]
                self.batt_Vmax = data["batt_conf"]["Vmax"]

                self.sensorAC_IN_Pin = data["peripherals"]["sensorAC_IN_Pin"]
                self.sensorAC_OUT_Pin = data["peripherals"]["sensorAC_OUT_Pin"]
                self.sensorDC_Pin = data["peripherals"]["sensorDC_Pin"]
                self.sensorTH_Pin = data["peripherals"]["sensorTH_Pin"]
                self.relayContact_Pin = data["peripherals"]["relayContact_Pin"]
                self.relayCharger_Pin = data["peripherals"]["relayCharger_Pin"]
                self.relayDif_Pin = data["peripherals"]["relayDif_Pin"]

                self.SD_CS = data["peripherals"]["SD_CS"]
                self.SD_MOSI = data["peripherals"]["SD_MOSI"]
                self.SD_MISO = data["peripherals"]["SD_MISO"]
                self.SD_SCK = data["peripherals"]["SD_SCK"]
