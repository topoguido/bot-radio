import json

class Configs:
    def __init__(self):

        with open("config.json", "r") as f:
            data =  json.load(f)

            self._user = data["update_params"]["user"]
            self._repo = data["update_params"]["repo"]
            self._branch = data["update_params"]["branch"]
            self._files = data["update_params"]["files"]
            self._working_dir = data["update_params"]["working_dir"]

