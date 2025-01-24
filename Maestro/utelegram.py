import urequests
import re
from temp import msg

class ubot:
    
    def __init__(self, token, debug):
        self.url = 'https://api.telegram.org/bot' + token
        self.default_handler = None
        self.command = None
        self.commandOK = False
        self.chat_id = ''
        self.chat_username = ''
        self.chat_name = ''
        self.debug = debug
        self.message_offset = self.get_msg_id()
        self.commands = self.getCommands()
        print(f'Lista de comandos: {self.commands}')
       
    def getCommands(self):
        commands = {}
        try:
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            if self.debug: print(f'URL: {self.url}')
            response = urequests.get(self.url + '/getMyCommands', headers=headers, timeout=20)
            if response.status_code == 200:
                response_json = response.json()
                if 'result' in response_json:
                    for item in response_json['result']:
                        command = '/' + item['command']
                        desc = item['description']
                        commands[command] = desc
                    return commands    
            else:
                print(f"Error HTTP: {response.status_code}")
                return None    
        except (ValueError):
            return None
        except (OSError):
            print("OSError: request timed out")
            return None
        except Exception as e:
            print(f"Error inesperado: {e}")
            return None
        finally:
            response.close()

    def reply_ping(self, chat_id):
        if self.debug: print('Respondiendo al ping')
        self.send(chat_id, 'pong')
    
    def saluda(self, chat_id):
        if self.debug: print('Saludando')
        self.send(int(chat_id), 'Hola, el bot se ha iniciado')
    
      
    def send(self, chat_id, text):
        data = {'chat_id': chat_id, 'text': text}
        try:
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            response = urequests.post(self.url + '/sendMessage', json=data, headers=headers)
            response.close()
            return True
        except:
            return False

    def read_messages(self):
        result = []
        self.query_updates = {
            'offset': self.message_offset + 1,
            'limit': 1,
            'timeout': 30,
            'allowed_updates': ['message']}
        try:
            update_messages = urequests.post(self.url + '/getUpdates', json=self.query_updates).json() 
            if 'result' in update_messages:
                if self.debug: print(f'Metodo read_messages: {update_messages}')
                for item in update_messages['result']:
                    result.append(item)
            return result
        except (ValueError):
            return None
        except (OSError):
            if self.debug: print("OSError: request timed out")
            return None

    def read_once(self):
        messages = self.read_messages()
        if messages:
            if self.debug: print('Mensajes entrantes')
            if self.message_offset==0:
                self.message_offset = messages[-1]['update_id']
                if self.debug: print(f'MSG_ID: {self.message_offset}')
                return self.message_handler(messages[-1])
            else:
                for message in messages:
                    if message['update_id'] >= self.message_offset:
                        self.message_offset = message['update_id']
                        if self.debug: print(f'MSG_ID: {self.message_offset}')
                        return self.message_handler(message)

    def message_handler(self, message):
        if 'text' in message['message']:
            parts = message['message']['text'].split(' ')
            self.update_temp('temp.py', self.message_offset )
            if 'entities' in message['message']:
                for entity in message['message']['entities']:
                    if 'type' in entity and entity['type'] == 'bot_command':
                        if parts[0] in self.commands:
                            if self.debug: print(f'Comando recibido: {parts[0]}')
                            self.command = parts[0]
                            self.commandOK = True
                            self.chat_id = message['message']['chat']['id']
                            self.chat_username = message['message']['chat']['username']
                            self.chat_name = message['message']['chat']['first_name']
                            return True

                        else:
                            self.commandOK = False
                            self.send(message['message']['chat']['id'], 'No reconozco ese comando \U0001F611')
                            return False
                    else:
                        print(f'Es un mensaje normal con el texto: {parts}')

    def update_temp(self, file_path, id_msg):
        with open(file_path, "r") as file:
            content = file.read()

        pattern = r"'ultimo_id_msg': *\d+"
        replacement = f"'ultimo_id_msg': {id_msg}"
        updated_content = re.sub(pattern, replacement, content)
        with open(file_path, "w") as file:
            file.write(updated_content)
    
    def get_msg_id(self):
        return msg['ultimo_id_msg']