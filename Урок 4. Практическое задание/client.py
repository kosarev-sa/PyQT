# Клиентская программа

import argparse
import sys
import json
import time
from socket import socket, AF_INET, SOCK_STREAM
from logging import getLogger
import threading

from client_db_alchemy import ClientDbAlchemy
from descriptors_classes import PortValidator, AddressValidator
from metaclasses_verifiers import ClientVerifier
from globals.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, \
    DEFAULT_IP_ADDRESS, DEFAULT_PORT, MESSAGE, SENDER, MESSAGE_TEXT, EXIT, DESTINATION, USERS_REQUEST, LIST_INFO, \
    ADD_CONTACT, GET_CONTACTS, REMOVE_CONTACT, CONTACT
from globals.utils import get_message, send_message
from log_config import client_log_config
from log_decors import log_dec

log = getLogger('client')

# Объект блокировки сокета и работы с базой данных
sock_lock = threading.Lock()
database_lock = threading.Lock()


@log_dec
def arg_parser():
    # Парсер аргументов коммандной строки
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])

    client_name = namespace.name
    # Пробуем загрузить параметры командной строки (например, client.py 192.168.0.7 8079)
    # Если нет параметров, то задаём значения по умоланию
    try:
        server_address = namespace.addr
        server_port = namespace.port
        # if not (server_port > 1023 or server_port < 65535):
        #     raise ValueError
    except IndexError:
        log.warning('server_address = DEFAULT_IP_ADDRESS, server_port = DEFAULT_PORT')
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
    # except ValueError:
    #     # print('Номер порта - число от 1024 до 65535.')
    #     log.error('exit(1). Номер порта - число от 1024 до 65535')
    #     sys.exit(1)
    return server_address, server_port, client_name


class Client(metaclass=ClientVerifier):
    server_port = PortValidator()
    server_address = AddressValidator()

    def __init__(self, server_address, server_port, database, account_name='Guest'):
        self.address = server_address
        self.port = server_port
        self.database = database
        self.account_name = account_name
        # Параметры сокета
        self.AF_INET = AF_INET
        self.SOCK_STREAM = SOCK_STREAM
        super().__init__()

    def create_msg(self, sock):
        # Функция запрашивает ввод получателя, ввод сообщения и возвращает словарь с данными сообщения
        to_user = input('Введите получателя сообщения: ')
        msg = input('Введите сообщение для отправки: ')
        # Проверяет, что получатель существует
        with database_lock:
            if not self.database.check_user(to_user):
                log.error(f'Попытка отправить сообщение незарегистрированому получателю: {to_user}')
                return
        msg_dct = {ACTION: MESSAGE,
                   SENDER: self.account_name,
                   DESTINATION: to_user,
                   MESSAGE_TEXT: msg,
                   TIME: time.time()
                   }
        log.debug(f'Подготовлены данные для сообщения: {msg_dct}')
        # Сохраняет сообщения для истории
        with database_lock:
            self.database.save_message(self.account_name , to_user, msg)
        # Необходимо дождаться освобождения сокета для отправки сообщения
        with sock_lock:
            try:
                send_message(sock, msg_dct)
                log.info(f'Отправлено сообщение -> {to_user}')
            except:
                log.critical('Потеряно соединение с сервером')
                sys.exit(1)

    def create_exit_msg(self):
        # Функция генерирует сообщение о выходе клиента
        user_exit_msg = {ACTION: EXIT,
                         TIME: time.time(),
                         USER:
                             {ACCOUNT_NAME: self.account_name}
                         }
        return user_exit_msg

    # Функция для вывода дополнительных команд
    def print_help(self):
        print('Дополнительные команды:')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')

    def user_interactive(self, sock):
        # Функция для получение команды от пользователя на отправку сообщений или завершение работы
        # Завершает работу при вводе комманды exit
        while True:
            print(self.account_name)
            aim = input(
                'Введите команду ("msg" - ввод получателя->Enter->текст сообщения для отправки, "help" - доп.команды, '
                'или "exit" - завершение работы):\n')
            if aim == "help":
                self.print_help()
            elif aim == 'msg':
                self.create_msg(sock)
            elif aim == 'exit':
                send_message(sock, self.create_exit_msg())
                log.info('Завершение работы по команде пользователя')
                print('Спасибо за использование нашего сервиса!')
                # Задержка для необходимого времени доставки сообщения о выходе
                time.sleep(1)
                break
            elif aim == 'contacts':
                with database_lock:
                    contacts_lst = self.database.get_contacts()
                for contact in contacts_lst:
                    print(contact)
            elif aim == 'edit':
                self.edit_contacts()
            elif aim == 'history':
                self.print_history()
            else:
                log.info('Неизвестная команда пользователя')
                print('Неизвестная команда, попробойте снова.')

    # Функция выводящяя историю сообщений
    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - нажать Enter: ')
        with database_lock:
            if ask == 'in':
                history_lst = self.database.get_msg_history(to_who=self.account_name)
                for message in history_lst:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_lst = self.database.get_msg_history(from_who=self.account_name)
                for message in history_lst:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_lst = self.database.get_msg_history()
                for message in history_lst:
                    print(f'\nСообщение от пользователя: {message[0]}, '
                          f'пользователю {message[1]} от {message[3]}\n{message[2]}')

    # Функция изменения контактов
    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    log.error('Попытка удаления несуществующего контакта')
        elif ans == 'add':
            # Проверка на возможность создания такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        self.add_contact(self.s, self.account_name, edit)
                    except ValueError:
                        log.error('Не удалось отправить информацию на сервер')

    def message_from_server(self, sock):
        # Обработчик сообщений других пользователей, поступающих с сервера.
        while True:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # Если не сделать тут задержку, то второй поток может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            with sock_lock:
                try:
                    msg = get_message(sock)
                    if ACTION in msg and msg[ACTION] == MESSAGE and MESSAGE_TEXT in msg \
                            and SENDER in msg and DESTINATION in msg and msg[DESTINATION] == self.account_name:
                        print(f'\nCообщение от {msg[SENDER]}: {msg[MESSAGE_TEXT]}')
                        log.info(f'Cообщение от {msg[SENDER]}: {msg[MESSAGE_TEXT]}')
                    else:
                        log.error(f'Некорректное сообщение с сервера: {msg}')
                except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    log.critical(f'Потеряно соединение с сервером')
                    break

    def create_presence_msg(self):
        # Функция генерирует сообщение о присутствии клиента
        # {'action': 'presence', 'time': 1642973242.1169634, 'user': {'account_name': 'Guest'}}
        user_presence_msg = {ACTION: PRESENCE,
                             TIME: time.time(),
                             USER:
                                 {ACCOUNT_NAME: self.account_name}
                             }
        return user_presence_msg

    def server_response_validator(self, msg):
        # Функция интерпретирует ответ сервера
        if RESPONSE in msg:
            if msg[RESPONSE] == 200:
                log.info('Клиент соединился с сервером. Подключение успешно')
                return '200 : OK'
            log.error('Клиент не подключен к серверу')
            return f'400 : {msg[ERROR]}'
        log.error('Клиент не подключен серверу')
        raise ValueError

    # Функция запроса списка известных пользователей
    def user_lst_request(self, sock, username):
        log.debug(f'Запрос списка известных пользователей {username}')
        req = {ACTION: USERS_REQUEST,
               TIME: time.time(),
               USER:
                   {ACCOUNT_NAME: username}
               }
        send_message(sock, req)
        ans = get_message(sock)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            return ans[LIST_INFO]
        else:
            raise ValueError

    # Функция добавления пользователя в контакт лист
    def add_contact(self, sock, username, contact):
        log.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER:
                {ACCOUNT_NAME: username},
            CONTACT: contact
        }
        send_message(sock, req)
        ans = get_message(sock)
        if RESPONSE in ans and ans[RESPONSE] == 200:
            pass
        else:
            raise ValueError('Ошибка создания контакта')
        print('Удачное создание контакта.')

    # Функция - запрос контакт листа
    def contacts_lst_request(self, sock, name):
        log.debug(f'Запрос контакт-листа для пользователся {name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER:
                {ACCOUNT_NAME: name}
        }
        log.debug(f'Сформирован запрос {req}')
        send_message(sock, req)
        ans = get_message(sock)
        log.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            return ans[LIST_INFO]
        else:
            raise ValueError

    # Функция удаления пользователя из контакт листа
    def remove_contact(self, sock, username, contact):
        log.debug(f'Создание контакта {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER:
                {ACCOUNT_NAME: username},
            ACCOUNT_NAME: contact
        }
        send_message(sock, req)
        ans = get_message(sock)
        if RESPONSE in ans and ans[RESPONSE] == 200:
            pass
        else:
            raise ValueError('Ошибка удаления клиента')
        print('Удачное удаление')

    # Функция - инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера
    def database_load(self, sock, database, username):
        # Загружает список известных пользователей
        try:
            users_lst = self.user_lst_request(sock, username)
        except ValueError:
            log.error('Ошибка запроса списка известных пользователей')
        else:
            database.add_known_users(users_lst)
        # Загружает список контактов
        try:
            contacts_lst = self.contacts_lst_request(sock, username)
        except ValueError:
            log.error('Ошибка запроса списка контактов')
        else:
            for contact in contacts_lst:
                database.add_contact(contact)

    def main_func(self):
        # Запрос имени пользователя, если ранее не задано
        if not self.account_name:
            self.account_name = input('Введите имя пользователя: ')
        try:
            self.s = socket(self.AF_INET, self.SOCK_STREAM)  # Создает сокет TCP (AF_INET — сетевой, SOCK_STREAM — потоковый)
            self.s.connect((self.address, self.port))

            msg_to_server = self.create_presence_msg()
            send_message(self.s, msg_to_server)  # Отправляет на сервер сообщение о присутствии клиента

            server_answer = self.server_response_validator(get_message(self.s))
            # print(server_answer)    # Код ответа сервера (200/400)
            log.info(f'Ответ сервера: "{server_answer}"')

        except (ValueError, json.JSONDecodeError):
            # print('Не удалось декодировать сообщение сервера.')
            log.error('Не удалось декодировать сообщение сервера')
        except ConnectionRefusedError:
            log.critical(f'Нет соединения с сервером {self.address}:{self.port}, отвергнут запрос на подключение')
            sys.exit(1)
        else:
            # Если соединение с сервером установлено корректно, загружаем данные в базу с сервера,
            # запускаем потоки приёма и отправки сообщений.

            # Основной цикл прогрммы:
            self.database_load(self.s, self.database, self.account_name)
            # Поток приёма сообщений
            recv_thr = threading.Thread(target=self.message_from_server, args=(self.s,))
            recv_thr.daemon = True
            recv_thr.start()

            # Поток отправки сообщений и взаимодействие с пользователем.
            send_thr = threading.Thread(target=self.user_interactive, args=(self.s,))
            send_thr.daemon = True
            send_thr.start()

            log.debug('Открыты потоки приёма и отправки сообщений')

            # Справка: Если один из потоков завершён, значит или потеряно соединение или пользователь ввёл exit.
            # Поскольку все события обработываются в 'демонических' потоках, достаточно просто завершить основной цикл.
            while True:
                time.sleep(1)
                if recv_thr.is_alive() and send_thr.is_alive():
                    continue
                break


@log_dec
def main():
    server_address, server_port, client_name = arg_parser()

    # Инициализация БД
    database = ClientDbAlchemy(client_name)

    # Экземпляр класса Клиент:
    client = Client(server_address, server_port, database, client_name)
    client.main_func()


if __name__ == '__main__':
    main()
