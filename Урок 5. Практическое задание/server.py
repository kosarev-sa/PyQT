# Серверная программа
import configparser
import os
import sys
import json
import threading
import time
from socket import socket, AF_INET, SOCK_STREAM
from logging import getLogger
import argparse
from select import select
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from descriptors_classes import PortValidator, AddressValidator
from globals.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, \
    DEFAULT_PORT, MESSAGE_TEXT, MESSAGE, SENDER, RESPONSE_200, RESPONSE_400, DESTINATION, EXIT, GET_CONTACTS, \
    RESPONSE_202, LIST_INFO, ADD_CONTACT, REMOVE_CONTACT, CONTACT, USERS_REQUEST
from globals.utils import get_message, send_message
from log_config import server_log_config
from log_decors import LogDecCls
from metaclasses_verifiers import ServerVerifier
from server_db_alchemy import ServerDbAlchemy
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow

log = getLogger('server')

# Флаг, что подключен новый пользователь (от постоянных запросов на обновление)
new_connection = False
con_flag_lock = threading.Lock()


@LogDecCls()
def arg_parser(default_port, default_address):
    # Парсер аргументов коммандной строки
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])

    # Пробуем загрузить параметры командной строки (например, server.py -p 8079 -a 192.168.0.7)
    # Если нет параметров, то задаём значения по умоланию

    # Порт:
    try:
        listen_port = namespace.p
        # if not (listen_port > 1023 or listen_port < 65535):
        #     raise ValueError
    except IndexError:
        # print('Проверьте номер порта. Пример указания параметров командной строки:\n'
        #       '(-\'p\' номер порта -\'a\' адрес, который будет слушать сервер).\n'
        #       'Parameters: -\'p\' 8079 -\'a\' 192.168.0.7.')
        log.critical('exit(1). Проверьте номер порта. Пример: Parameters: -\'p\' 8079 -\'a\' 192.168.0.7')
        sys.exit(1)
    # except ValueError:
    #     # print('Номер порта - число от 1024 до 65535.')
    #     log.critical('exit(1). Номер порта - число от 1024 до 65535')
    #     sys.exit(1)

    # IP-адрес:
    try:
        listen_address = namespace.a
    except IndexError:
        # print('Проверьте IP-адрес. Пример указания параметров командной строки:\n'
        #       '(-\'p\' номер порта -\'a\' адрес, который будет слушать сервер).\n'
        #       'Parameters: -\'p\' 8079 -\'a\' 192.168.0.7.')
        log.critical('exit(1). Проверьте IP-адрес. Пример: Parameters: -\'p\' 8079 -\'a\' 192.168.0.7')
        sys.exit(1)

    return listen_address, listen_port


class Server(threading.Thread, metaclass=ServerVerifier):
    listen_port = PortValidator()
    listen_address = AddressValidator()

    def __init__(self, listen_address, listen_port, database):
        # Параметры подключения
        self.listen_address = listen_address
        self.listen_port = listen_port
        # Параметры сокета
        self.AF_INET = AF_INET
        self.SOCK_STREAM = SOCK_STREAM
        # Список клиентов
        self.clients = []
        # Список (очередь) сообщений
        self.messages = []
        # Словарь имен пользователей и соответствующих им сокетов
        self.users_names = {}
        # База данных сервера
        self.database = database
        # Конструктор предка
        super().__init__()

    def socket_create(self):
        s = socket(self.AF_INET, self.SOCK_STREAM)  # Создает сокет TCP (AF_INET — сетевой, SOCK_STREAM — потоковый)
        s.bind((self.listen_address, self.listen_port))
        s.settimeout(0.5)
        self.s = s
        self.s.listen(
            MAX_CONNECTIONS)  # Переходит в режим ожидания запросов, одновременно обслуживает не более MAX_CONNECTIONS
        log.info(f'Готовность к соединению')

    def run(self):
        self.socket_create()

        # Основной цикл программы
        while True:
            # Ожидание подключения. Если таймаут вышел, ловит исключение
            try:
                client, client_address = self.s.accept()  # Принять запрос на соединение
            except OSError:
                pass
            else:
                log.info(f'Установлено соедение с {client_address}')
                self.clients.append(client)

            recv_lst = []
            send_lst = []
            err_lst = []

            # Проверяет на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_lst, send_lst, err_lst = select(self.clients, self.clients, [], 0)
            except OSError as err:
                log.error(f'Ошибка работы с сокетами: {err}')

            # Сервер принимает данные. Если там есть сообщения, кладёт в словарь. Если ошибка, исключает клиента.
            if recv_lst:
                for r_client in recv_lst:
                    try:
                        self.client_message_validator(get_message(r_client), r_client)
                    except:
                        log.info(f'Клиент {r_client.getpeername()} отключился от сервера')
                        for name in self.users_names:
                            if self.users_names[name] == r_client:
                                self.database.user_logout(name)
                                del self.users_names[name]
                                break
                        self.clients.remove(r_client)

            # Обрабатываем каждое сообщение, если они есть
            for msg in self.messages:
                try:
                    self.send_address_message(msg, send_lst)
                except:
                    log.info(f'Связь с клиентом {msg[DESTINATION]} потеряна')
                    self.clients.remove(self.users_names[msg[DESTINATION]])
                    self.database.user_logout(msg[DESTINATION])
                    del self.users_names[msg[DESTINATION]]
            self.messages.clear()

    def send_address_message(self, msg, w_socks):
        # Отправка сообщения определённому клиенту.
        # Принимает сообщение, список зарегистрированых пользователей и сокеты на запись (слушающие).
        # Ничего не возвращает.
        if msg[DESTINATION] in self.users_names and self.users_names[msg[DESTINATION]] in w_socks:
            send_message(self.users_names[msg[DESTINATION]], msg)
            log.info(f'Сообщение отправлено -> {msg[DESTINATION]} от: {msg[SENDER]}')
        elif msg[DESTINATION] in self.users_names and self.users_names[msg[DESTINATION]] not in w_socks:
            raise ConnectionError
        else:
            log.error(
                f'Пользователь {msg[DESTINATION]} не зарегистрирован на сервере, отправка сообщения невозможна')

    def client_message_validator(self, msg, client):
        global new_connection
        # Если это сообщение о присутствии, принимает и отвечает, если успех
        # Валидатор проверяет корректность словаря, переданного сообщением клиента
        # (наличие [ACTION]==PRESENCE, [USER][ACCOUNT_NAME]=='Guest', TIME)
        if ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg and USER in msg:
            # Если пользователь не зарегистрирован, регистрирует, иначе отправляет ответ и завершает соединение.
            if msg[USER][ACCOUNT_NAME] not in self.users_names.keys():
                log.info('Соединение с сервером клиента %s. Успешно' % msg[USER][ACCOUNT_NAME])
                self.users_names[msg[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(msg[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
                with con_flag_lock:
                    new_connection = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'Указанное имя пользователя занято'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        # Если это сообщение не о присутствии, то добавляет его в очередь сообщений. Ответ не требуется
        elif ACTION in msg and msg[ACTION] == MESSAGE and MESSAGE_TEXT in msg \
                and SENDER in msg and DESTINATION in msg and TIME in msg:
            self.messages.append(msg)
            self.database.msg_counter(msg[SENDER], msg[DESTINATION])
            return
        # Если клиент выходит
        elif ACTION in msg and msg[ACTION] == EXIT and USER in msg:
            self.database.user_logout(msg[USER][ACCOUNT_NAME])
            log.info('Соединение с сервером клиента %s разорвано' % msg[USER][ACCOUNT_NAME])
            self.clients.remove(self.users_names[msg[USER][ACCOUNT_NAME]])
            self.users_names[msg[USER][ACCOUNT_NAME]].close()
            del self.users_names[msg[USER][ACCOUNT_NAME]]
            with con_flag_lock:
                new_connection = True
            return
        # Если это запрос контакт-листа
        elif ACTION in msg and msg[ACTION] == GET_CONTACTS and USER in msg \
                and self.users_names[msg[USER][ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(msg[USER][ACCOUNT_NAME])
            send_message(client, response)
        # Если это добавление контакта
        elif ACTION in msg and msg[ACTION] == ADD_CONTACT and CONTACT in msg and USER in msg \
                and self.users_names[msg[USER][ACCOUNT_NAME]] == client:
            self.database.add_contact(msg[USER][ACCOUNT_NAME], msg[CONTACT])
            send_message(client, RESPONSE_200)
        # Если это удаление контакта
        elif ACTION in msg and msg[ACTION] == REMOVE_CONTACT and CONTACT in msg and USER in msg \
                and self.users_names[msg[USER][ACCOUNT_NAME]] == client:
            self.database.remove_contact(msg[USER][ACCOUNT_NAME], msg[CONTACT])
            send_message(client, RESPONSE_200)
        # Если это запрос известных пользователей
        elif ACTION in msg and msg[ACTION] == USERS_REQUEST and USER in msg \
                and self.users_names[msg[USER][ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_lst()]
            send_message(client, response)
        # Иначе 'Bad request'
        else:
            response = RESPONSE_400
            response[ERROR] = 'Некорректный запрос.'
            send_message(client, response)
            return


def main():
    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    # Загрузка параметров командной строки, если нет параметров, то задаём значения по умоланию.
    listen_address, listen_port = arg_parser(config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    # Инициализация базы данных
    database = ServerDbAlchemy(os.path.join(config['SETTINGS']['Database_path'], config['SETTINGS']['Database_file']))

    # Экземпляр класса Сервера:
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()  # Запуск в отдельном потоке

    # Графическое окуружение для сервера:
    server_app = QApplication(sys.argv)     # Создается приложение
    main_window = MainWindow()              # ЗАПУСК РАБОТАЕТ ПАРАЛЕЛЬНО СЕРВЕРА К ОКНУ
                                            # В ГЛАВНОМ ПОТОКЕ ЗАПУСКАЕТСЯ GUI - ГРАФИЧЕСКИЙ ИНТЕРФЕЙС ПОЛЬЗОВАТЕЛЯ

    # Инициализируются параметры главного окна
    main_window.statusBar().showMessage('Server running')                   # Подвал
    main_window.active_clients_table.setModel(gui_create_model(database))   # Заполняем таблицу основного окна,
    main_window.active_clients_table.resizeColumnsToContents()              # делаем разметку и заполянем ее
    main_window.active_clients_table.resizeRowsToContents()

    # Функция обновляет список подключённых, проверяет флаг подключения, и если надо обновляет список
    def lst_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with con_flag_lock:
                new_connection = False

    # Функция создает окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        # stat_window.show()

    # Функция создает окно с настройками сервера
    def server_config():
        global config_window
        # Создаёт окно и заносит в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка!', 'Порт должен быть числом (от 1024 до 65535)!')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(config_window, 'OK!', 'Настройки успешно сохранены!')
            else:
                message.warning(config_window, 'Ошибка!', 'Порт должен быть числом (от 1024 до 65535)!')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(lst_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(lst_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()


if __name__ == '__main__':
    main()
