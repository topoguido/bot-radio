import urequests, json, gc
import mylib
from Bot_configurations import Bot_configurations

class ubot:
    
    def __init__(self, debug):
        self.config = Bot_configurations()
        self.url = 'https://api.telegram.org/bot' + self.config.token
        self.command = None
        self.commandOK = False
        self.chat_id = ''
        self.chat_username = ''
        self.chat_name = ''
        self.debug = debug
        self.message_offset = None
        self.commands = None
        self.greeting = False
        self.get_updates_failed = False
        self.get_updates_failures = 0
        
       
    def getCommands(self):
        commands = {}
        response = None
        response_json = None
        headers = None
        try:
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            mylib.log_print("Get Commands", level=mylib.DEBUG)
            gc.collect()
            response = urequests.get(self.url + '/getMyCommands', headers=headers, timeout=10)
            if response.status_code == 200:
                response_json = response.json()
                if 'result' in response_json:
                    for item in response_json['result']:
                        command = '/' + item['command']
                        desc = item['description']
                        commands[command] = desc
                        self.commands = commands
                    return commands    
            else:
                mylib.log_print(
                    f"Error HTTP: {response.status_code}",
                    level=mylib.ERROR,
                )
                return None    
        except (ValueError):
            return None
        except (OSError) as e:
            mylib.log_print(
                "OSError en getCommands: " + str(e),
                level=mylib.WARNING,
                exception=e,
            )
            return None
        except Exception as e:
            mylib.log_print(
                f"Error inesperado: {e}",
                level=mylib.ERROR,
                exception=e,
            )
            return None
        finally:
            if response is not None:
                response.close()
            response = None
            response_json = None
            headers = None
            gc.collect()

    def reply_ping(self, chat_id):
        return self.send(chat_id, 'pong')
    
    def saluda(self):
        return self.send(int(self.config.chat_id_default), 'El bot se ha iniciado')
        #return self.send(int(self.config.group_id_default), 'El bot se ha iniciado')
    
      
    def send(self, chat_id, text):
        response = None
        data = {'chat_id': chat_id, 'text': text}
        payload = None
        headers = None
        try:
            payload = json.dumps(data).encode("utf-8")
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            }

            gc.collect()
            response = urequests.post(
                self.url + "/sendMessage",
                data=payload,
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                return True
            else:
                mylib.log_print(
                    f"Metodo send no puede enviar: {response.status_code}",
                    level=mylib.ERROR,
                )
                mylib.log_print("Telegram:", response.text, level=mylib.ERROR)
                return False
        except OSError as e:
            mylib.log_print(
                'Metodo bot.send:',
                e,
                level=mylib.ERROR,
                exception=e,
            )
            return False
        
        finally:
            if response is not None:
                response.close()
            response = None
            data = None
            payload = None
            headers = None
            gc.collect()

    def read_once(self):
        messages = self.get_messages()
        if messages:
            if self.message_offset == 0:
                self.message_offset = messages[-1]['update_id']
                return self.message_handler(messages[-1])
            else:
                for message in messages:
                    if message['update_id'] >= self.message_offset:
                        self.message_offset = message['update_id']
                        return self.message_handler(message)

    def _register_get_updates_failure(self, message, exception=None):
        self.get_updates_failures += 1
        if not self.get_updates_failed:
            mylib.log_print(
                message,
                level=mylib.WARNING,
                exception=exception,
            )
            self.get_updates_failed = True

    def _register_get_updates_success(self):
        if self.get_updates_failed:
            mylib.log_print("Conexion con Telegram recuperada")
        self.get_updates_failed = False
        self.get_updates_failures = 0

    def get_messages(self, offset=None):
        result = []
        response = None
        update_messages = {}
        if offset is not None :
            new_offset = offset
        else:
            new_offset = self.message_offset + 1

        params = [
            'offset={}'.format(new_offset),
            'limit=1',
            'timeout=5',
            'allowed_updates=message'
        ]

        try:
            url = self.url + '/getUpdates?' + '&'.join(params)
            gc.collect()
            response = urequests.get(url, timeout=12)
            if response.status_code == 200:
                update_messages = response.json()
                if 'result' in update_messages:
                    self._register_get_updates_success()
                    for item in update_messages['result']:
                        result.append(item)
                else:
                    self._register_get_updates_failure(
                        "Respuesta de Telegram sin result en getUpdates"
                    )
                    return None
            else:
                self._register_get_updates_failure(
                    f"Error HTTP en getUpdates: {response.status_code}"
                )
            return result
        except ValueError as e:
            self._register_get_updates_failure(
                "Respuesta invalida de Telegram en getUpdates: " + repr(e),
                exception=e,
            )
            return None
        except (OSError) as e:
            self._register_get_updates_failure(
                "OSError en get_messages: " + str(e),
                exception=e,
            )
            return None
        finally:
            if response is not None:
                response.close()
            response = None
            gc.collect()


    def message_handler(self, message):
        msg = message.get('message')
        if not msg:
            return False

        text = msg.get('text')
        if not text:
            return False
        
        parts = text.split('@')[0]
        self.update_temp(self.message_offset )
        entities = msg.get('entities', [])
        if not entities:
            return False
        
        for entity in entities:
            if 'type' in entity and entity.get('type') == 'bot_command':
                if parts in self.commands:
                    mylib.log_print(f'Comando recibido: {parts}')
                    self.command = parts
                    self.commandOK = True

                    chat = msg.get('chat', {})
                    from_user = msg.get('from', {})

                    if chat.get('type') == "private":
                        self.chat_id = chat.get('id', '')
                        self.chat_username = chat.get('username','')
                        self.chat_name = chat.get('first_name','')
                    
                    elif chat.get('type') in ["group", "supergroup"]:
                        self.chat_id = chat.get('id', '')
                        self.chat_name = from_user.get('first_name', '')
                        self.chat_username = from_user.get('username', '')
                        
                    return True

                else:
                    self.commandOK = False
                    return False
        
    def update_temp(self, id_msg):
        try:
            with open("temp.json", "r") as file:
                data = json.load(file)
            
        except (OSError, ValueError):
            data = {}
        data["ultimo_id_msg"] = id_msg
        
        with open("temp.json", "w") as file:
            json.dump(data, file)
    
    def get_msg_id(self):
        try:
            with open("temp.json", "r") as f:
                temp = json.load(f)
                self.message_offset = temp["ultimo_id_msg"]

        except (OSError, ValueError) as e:
            messages =  self.get_messages(offset = -1)
            if messages is not None:
                if len(messages) > 0:
                    id_msg = int(messages[0]['update_id'])
                else:
                    id_msg = 1
                
                var = {"ultimo_id_msg": id_msg}
                with open("temp.json", "w") as f:
                    json.dump(var, f)
                self.message_offset =  id_msg
            else:
                self.message_offset = 1

    def test_connection(self):
        response = None
        try:
            gc.collect()
            response = urequests.get(self.url + '/getMe', timeout=5)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception:
            return False
        finally:
            if response is not None:
                response.close()
            response = None
            gc.collect()
