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
                self.mac_sensortx = data["wlan_com"]["mac_sensortx"]
                self.reset_delay = data["device_conf"]["reset_delay"]



