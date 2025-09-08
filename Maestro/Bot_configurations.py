import json

class Bot_configurations:

    def __init__(self):

        with open("bot_config.json", "r") as f:
            data =  json.load(f)
            self.token = data["token"]
            self.chat_id_default = data["chat_id_default"]


