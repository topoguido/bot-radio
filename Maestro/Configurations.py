import json

class Configurations:

    def __init__(self, type):

        with open("config.json", "r") as f:
            data =  json.load(f)

            self.debug = data["debug"]

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

                self.server = data["mqtt_conf"]["server"]
                self.port = data["mqtt_conf"]["port"]
                self.client_id = data["mqtt_conf"]["client_id"].encode()
                self.topic_cmd = data["mqtt_conf"]["topic_cmd"].encode()
                self.topic_status = data["mqtt_conf"]["topic_status"].encode()
                self.topic_resp  = data["mqtt_conf"]["topic_resp"].encode()



