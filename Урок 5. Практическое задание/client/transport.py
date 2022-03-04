from socket import socket, AF_INET, SOCK_STREAM
import sys
import time
from logging import getLogger
import json
import threading
from PyQt5.QtCore import pyqtSignal, QObject

from globals.utils import send_message, get_message
from globals.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, MESSAGE, SENDER, DESTINATION, \
    MESSAGE_TEXT, GET_CONTACTS, LIST_INFO, USERS_REQUEST, ADD_CONTACT, CONTACT, REMOVE_CONTACT, EXIT
from globals.errors import ServerError

sys.path.append('../')

log = getLogger('client')
socket_lock = threading.Lock()


# Для взаимодействия с сервером класс - Транспорт
class ClientTransport(threading.Thread, QObject):
    # Сигналы: новое сообщение и потеря соединения
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, address, database, username):
        threading.Thread.__init__(self)     # Вызываем конструктор предка
        QObject.__init__(self)              # Вызываем конструктор предка

        self.db = database
        self.username = username
        self.s = None
        self.connection_init(port, address)
        # Обновляет таблицы известных пользователей и контактов
        try:
            self.users_lst_update()
            self.contacts_lst_update()
        except OSError as err:
            if err.errno:
                log.critical(f'Потеряно соединение с сервером')
                raise ServerError('Потеряно соединение с сервером')
            log.error('Timeout соединения при обновлении списков пользователей')
        except json.JSONDecodeError:
            log.critical(f'Потеряно соединение с сервером')
            raise ServerError('Потеряно соединение с сервером')
        # Флаг продолжения работы транспорта
        self.running = True

    def connection_init(self, port, ip):
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.settimeout(5)        # Таймаут для освобождения сокета

        connected = False
        for i in range(5):       # Соединяемся, 5 попыток соединения, флаг успеха ставим в True если удалось
            log.info(f'Попытка подключения №{i + 1}')
            try:
                self.s.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:       # Если соединится не удалось - исключение
            log.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')
        log.debug('Установлено соединение с сервером')

        # Посылаем серверу приветственное сообщение и получаем ответ что всё нормально или ловим исключение
        try:
            with socket_lock:
                send_message(self.s, self.create_presence_msg())
                self.server_response_validator(get_message(self.s))
        except (OSError, json.JSONDecodeError):
            log.critical('Потеряно соединение с сервером')
            raise ServerError('Потеряно соединение с сервером')
        log.info('Соединение с сервером успешно установлено.')

    def create_presence_msg(self):
        # Функция генерирует сообщение о присутствии клиента (для сервера)
        # {'action': 'presence', 'time': 1642973242.1169634, 'user': {'account_name': 'Guest'}}
        user_presence_msg = {ACTION: PRESENCE,
                             TIME: time.time(),
                             USER:
                                 {ACCOUNT_NAME: self.username}
                             }
        log.debug(f'Сформировано {PRESENCE} сообщение для пользователя {self.username}')
        return user_presence_msg

    def server_response_validator(self, msg):
        # Функция интерпретирует ответ сервера. Если это подтверждение чего-либо:
        if RESPONSE in msg:
            if msg[RESPONSE] == 200:
                return
            elif msg[RESPONSE] == 400:
                raise ServerError(f'{msg[ERROR]}')
            else:
                log.debug(f'Принят неизвестный код подтверждения {msg[RESPONSE]}')
        # Если это сообщение от пользователя добавляем в базу, даём сигнал о новом сообщении
        elif ACTION in msg and msg[ACTION] == MESSAGE and SENDER in msg and DESTINATION in msg and MESSAGE_TEXT in msg \
                and msg[DESTINATION] == self.username:
            log.debug(f'Получено сообщение от пользователя {msg[SENDER]}:{msg[MESSAGE_TEXT]}')
            self.db.save_message(msg[SENDER], 'in', msg[MESSAGE_TEXT])
            self.new_message.emit(msg[SENDER])

    # Функция - запрос контакт листа
    def contacts_lst_update(self):
        log.debug(f'Запрос контакт-листа для пользователся {self.username}')
        req = {ACTION: GET_CONTACTS,
               TIME: time.time(),
               USER:
                   {ACCOUNT_NAME: self.username}
               }
        log.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_message(self.s, req)
            ans = get_message(self.s)
        log.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.db.add_contact(contact)
        else:
            log.error('Не удалось обновить список контактов')
            raise ValueError

    # Функция запроса списка известных пользователей
    def users_lst_update(self):
        log.debug(f'Запрос списка известных пользователей {self.username}')
        req = {ACTION: USERS_REQUEST,
               TIME: time.time(),
               USER:
                   {ACCOUNT_NAME: self.username}
               }
        send_message(self.s, req)
        ans = get_message(self.s)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.db.add_known_users(ans[LIST_INFO])
        else:
            log.error('Не удалось обновить список известных пользователей')
            raise ValueError

    # Функция добавления пользователя в контакт лист (сообщает на сервер)
    def add_contact(self, contact):
        log.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER:
                {ACCOUNT_NAME: self.username},
            CONTACT: contact
            }
        with socket_lock:
            send_message(self.s, req)
            self.server_response_validator(get_message(self.s))

    # Функция удаления пользователя из контакт листа (на сервере)
    def remove_contact(self, contact):
        log.debug(f'Удаление контакта {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER:
                {ACCOUNT_NAME: self.username},
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.s, req)
            self.server_response_validator(get_message(self.s))

    def create_exit_msg(self):
        # Функция генерирует сообщение о выходе клиента
        self.running = False
        user_exit_msg = {ACTION: EXIT,
                         TIME: time.time(),
                         USER:
                             {ACCOUNT_NAME: self.username}
                         }
        with socket_lock:
            try:
                send_message(self.s, user_exit_msg)
            except OSError:
                pass
        log.debug('Соккет закрывается (транспорт завершает работу)')
        time.sleep(0.5)

    # Функция отправки сообщения на сервер
    def create_send_message(self, to, msg):
        msg_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: msg
        }
        log.debug(f'Сформирован словарь сообщения: {msg_dict}')
        # Необходимо дождаться освобождения сокета для отправки сообщения
        with socket_lock:
            send_message(self.s, msg_dict)
            self.server_response_validator(get_message(self.s))
            log.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        log.debug('Запущен процесс - приёмник собщений с сервера')
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет, иначе отправка может долго ждать освобождения сокета.
            time.sleep(1)
            with socket_lock:
                try:
                    self.s.settimeout(0.5)
                    msg = get_message(self.s)
                except OSError as err:
                    if err.errno:
                        log.critical(f'Потеряно соединение с сервером')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    log.debug(f'Потеряно соединение с сервером')
                    self.running = False
                    self.connection_lost.emit()
                # Если сообщение получено, то вызываем функцию обработчик:
                else:
                    log.debug(f'Принято сообщение с сервера: {msg}')
                    self.server_response_validator(msg)
                finally:
                    self.s.settimeout(5)
