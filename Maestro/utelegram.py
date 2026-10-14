import urequests, json
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
        
       
    def getCommands(self):
        commands = {}
        response = None
        try:
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            mylib.log_print("Get Commands", level=mylib.DEBUG)
            response = urequests.get(self.url + '/getMyCommands', headers=headers, timeout=25)
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
                response.close()
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
            pass

    def reply_ping(self, chat_id):
        mylib.log_print('Respondiendo al ping', level=mylib.DEBUG)
        self.send(chat_id, 'pong')
    
    def saluda(self):
        mylib.log_print('Saludando', level=mylib.DEBUG)
        self.send(int(self.config.chat_id_default), 'Hola, el bot se ha iniciado')
        #self.send(int(self.config.group_id_default), 'Hola, el bot se ha iniciado')
    
      
    def send(self, chat_id, text):
        response = None
        data = {'chat_id': chat_id, 'text': text}
        try:
            payload = json.dumps(data).encode("utf-8")
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            }

            response = urequests.post(
                self.url + "/sendMessage",
                data=payload,
                headers=headers,
                timeout=5,
            )

            if response.status_code == 200:
                mylib.log_print(
                    f"Mensaje enviado: {data['text']}",
                    level=mylib.DEBUG,
                )
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

    def read_once(self):
        messages = self.get_messages()
        mylib.log_print('metodo read_once:', messages, level=mylib.DEBUG)
        if messages:
            mylib.log_print('Mensajes entrantes', level=mylib.DEBUG)
            if self.message_offset == 0:
                self.message_offset = messages[-1]['update_id']
                mylib.log_print(f'MSG_ID: {self.message_offset}', level=mylib.DEBUG)
                return self.message_handler(messages[-1])
            else:
                for message in messages:
                    if message['update_id'] >= self.message_offset:
                        self.message_offset = message['update_id']
                        mylib.log_print(
                            f'MSG_ID: {self.message_offset}',
                            level=mylib.DEBUG,
                        )
                        return self.message_handler(message)

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
            mylib.log_print('Haciendo getUpdates', level=mylib.DEBUG)
            response = urequests.get(url, timeout=8)
            if response.status_code == 200:
                update_messages = response.json()
                if 'result' in update_messages:
                    mylib.log_print(
                        f'Metodo get_messages: {update_messages}',
                        level=mylib.DEBUG,
                    )
                    for item in update_messages['result']:
                        result.append(item)
            return result
        except (ValueError):
            return None
        except (OSError) as e:
            mylib.log_print(
                "OSError en get_messages: " + str(e),
                level=mylib.DEBUG,
            )
            return None
        finally:
            if response is not None:
                response.close()


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
                    mylib.log_print(f'Comando recibido: {parts}', level=mylib.DEBUG)
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
        
        mylib.log_print(f'Es un mensaje normal con el texto: {parts}')

    def update_temp(self, id_msg):
        mylib.log_print(f'Metodo update_temp(id={id_msg})', level=mylib.DEBUG)
        try:
            with open("temp.json", "r") as file:
                data = json.load(file)
            
        except (OSError, ValueError):
            data = {}
        data["ultimo_id_msg"] = id_msg
        
        with open("temp.json", "w") as file:
            json.dump(data, file)
    
    def get_msg_id(self):
        mylib.log_print('Metodo get_msg_id()', level=mylib.DEBUG)
        try:
            with open("temp.json", "r") as f:
                temp = json.load(f)
                mylib.log_print(
                    f'Metodo get_msg_id() - archivo existente, datos: {temp}',
                    level=mylib.DEBUG,
                )
                self.message_offset = temp["ultimo_id_msg"]

        except (OSError, ValueError) as e:
            mylib.log_print(f'Excepcion: {e}', level=mylib.DEBUG)
            mylib.log_print(
                'Metodo get_msg_id() - Archivo no existe. Recuperando ultimo mensaje de telegram',
                level=mylib.DEBUG,
            )
            messages =  self.get_messages(offset = -1)
            if messages is not None:
                mylib.log_print(f'Mensaje {messages}', level=mylib.DEBUG)
                
                if len(messages) > 0:
                    id_msg = int(messages[0]['update_id'])
                else:
                    id_msg = 1
                
                mylib.log_print(f'El id capturado es: {id_msg}', level=mylib.DEBUG)
                var = {"ultimo_id_msg": id_msg}
                mylib.log_print(f'json a escribir {var}', level=mylib.DEBUG)
                with open("temp.json", "w") as f:
                    json.dump(var, f)
                self.message_offset =  id_msg
            else:
                self.message_offset = 1

    def test_connection(self):
        response = None
        try:
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
