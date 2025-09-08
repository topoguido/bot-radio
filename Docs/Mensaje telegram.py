# Este es un ejemplo de la respuesta de la API cuando se le piden
# los mensajes nuevos.

{
    'result': [
        {
            'update_id': 941431717, 
            'message': {
                    'message_id': 846, 
                    'from': {
                        'first_name': 'Emiliano Guido', 
                        'is_bot': False, 
                        'language_code': 'es', 
                        'id': 677317280, 
                        'username': 'LU6EAG'
                    }, 
                    'text': '/saluda', 
                    'date': 1737229073, 
                    'entities': [
                        {
                            'offset': 0, 
                            'length': 7, 
                            'type': 'bot_command'
                        }
                    ], 
                    'chat': {
                        'id': 677317280, 
                        'username': 'LU6EAG', 
                        'type': 'private', 
                        'first_name': 'Emiliano Guido'
                    }
                }
        }
    ], 
    'ok': True
}