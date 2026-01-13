import json

class Configs:
    def __init__(self):

        with open("pc/config.json", "r") as f:
            data =  json.load(f)
            self._status = data["update_params"]["status"]
            self._user = data["update_params"]["user"]
            self._repo = data["update_params"]["repo"]
            self._branch = data["update_params"]["branch"]
            self._files = data["update_params"]["files"]
            self._working_dir = data["update_params"]["working_dir"]

    def get_status(self):
        return self._status