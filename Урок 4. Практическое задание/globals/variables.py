# Глобальные константы

# Порт по умолчанию для сетевого ваимодействия
DEFAULT_PORT = 7777
# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_ADDRESS = '127.0.0.1'
# Максимальная очередь подключений
MAX_CONNECTIONS = 5
# Максимальная длинна сообщения в байтах
MAX_MSG_SIZE = 1024
# Кодировка проекта
ENCODING = 'utf-8'

# Прококол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'
CONTACT = 'contact'

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
EXIT = 'exit'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'

# Ответы сервера:
RESPONSE_200 = {RESPONSE: 200}
RESPONSE_400 = {RESPONSE: 400,
                ERROR: None}
RESPONSE_202 = {RESPONSE: 202,
                LIST_INFO: None}

# БД SQLite для соединения:
DATABASE = 'sqlite:///server_database.db3'
