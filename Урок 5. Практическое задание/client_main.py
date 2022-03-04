# Клиентская программа

from logging import getLogger
import log_config.client_log_config
import argparse
import sys
from PyQt5.QtWidgets import QApplication


from globals.variables import *
from globals.errors import ServerError
from log_decors import log_dec
from client.client_db_alchemy import ClientDbAlchemy
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog

log = getLogger('client')


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


if __name__ == '__main__':
    # Загружаем параметы коммандной строки
    server_address, server_port, client_name = arg_parser()
    # Создаём клиентокое приложение
    client_app = QApplication(sys.argv)
    # Если имя пользователя не было указано в командной строке то запросим его
    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект, иначе выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    # Записываем логи
    log.info(f'Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, '
             f'имя пользователя: {client_name}')
    # Создаём объект базы данных
    database = ClientDbAlchemy(client_name)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        s = ClientTransport(server_port, server_address, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    s.daemon = True
    s.start()

    # Создаём GUI
    main_window = ClientMainWindow(database, s)
    main_window.make_connection(s)
    main_window.setWindowTitle(f'Чат GB-SK-release: {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    s.create_exit_msg()
    s.join()


# Код без GUI, при этом часть методов перенесена в "./client.transport.py"
# class Client(metaclass=ClientVerifier):
#     server_port = PortValidator()
#     server_address = AddressValidator()
#
#     def __init__(self, server_address, server_port, database, account_name='Guest'):
#         self.address = server_address
#         self.port = server_port
#         self.database = database
#         self.account_name = account_name
#         # Параметры сокета
#         self.AF_INET = AF_INET
#         self.SOCK_STREAM = SOCK_STREAM
#         super().__init__()
#
#     # Функция для вывода дополнительных команд
#     def print_help(self):
#         print('Дополнительные команды:')
#         print('history - история сообщений')
#         print('contacts - список контактов')
#         print('edit - редактирование списка контактов')
#
#     def user_interactive(self, sock):
#         # Функция для получение команды от пользователя на отправку сообщений или завершение работы
#         # Завершает работу при вводе комманды exit
#         while True:
#             print(self.account_name)
#             aim = input(
#                 'Введите команду ("msg" - ввод получателя->Enter->текст сообщения для отправки, "help" - доп.команды, '
#                 'или "exit" - завершение работы):\n')
#             if aim == "help":
#                 self.print_help()
#             elif aim == 'msg':
#                 self.create_msg(sock)
#             elif aim == 'exit':
#                 send_message(sock, self.create_exit_msg())
#                 log.info('Завершение работы по команде пользователя')
#                 print('Спасибо за использование нашего сервиса!')
#                 # Задержка для необходимого времени доставки сообщения о выходе
#                 time.sleep(1)
#                 break
#             elif aim == 'contacts':
#                 with database_lock:
#                     contacts_lst = self.database.get_contacts()
#                 for contact in contacts_lst:
#                     print(contact)
#             elif aim == 'edit':
#                 self.edit_contacts()
#             elif aim == 'history':
#                 self.print_history()
#             else:
#                 log.info('Неизвестная команда пользователя')
#                 print('Неизвестная команда, попробойте снова.')
#
#     # Функция выводящяя историю сообщений
#     def print_history(self):
#         ask = input('Показать входящие сообщения - in, исходящие - out, все - нажать Enter: ')
#         with database_lock:
#             if ask == 'in':
#                 history_lst = self.database.get_msg_history(to_who=self.account_name)
#                 for message in history_lst:
#                     print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
#             elif ask == 'out':
#                 history_lst = self.database.get_msg_history(from_who=self.account_name)
#                 for message in history_lst:
#                     print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
#             else:
#                 history_lst = self.database.get_msg_history()
#                 for message in history_lst:
#                     print(f'\nСообщение от пользователя: {message[0]}, '
#                           f'пользователю {message[1]} от {message[3]}\n{message[2]}')
#
#     # Функция изменения контактов
#     def edit_contacts(self):
#         ans = input('Для удаления введите del, для добавления add: ')
#         if ans == 'del':
#             edit = input('Введите имя удаляемого контакта: ')
#             with database_lock:
#                 if self.database.check_contact(edit):
#                     self.database.del_contact(edit)
#                 else:
#                     log.error('Попытка удаления несуществующего контакта')
#         elif ans == 'add':
#             # Проверка на возможность создания такого контакта
#             edit = input('Введите имя создаваемого контакта: ')
#             if self.database.check_user(edit):
#                 with database_lock:
#                     self.database.add_contact(edit)
#                 with sock_lock:
#                     try:
#                         self.add_contact(self.s, self.account_name, edit)
#                     except ValueError:
#                         log.error('Не удалось отправить информацию на сервер')
#
#     def message_from_server(self, sock):
#         # Обработчик сообщений других пользователей, поступающих с сервера.
#         while True:
#             # Отдыхаем секунду и снова пробуем захватить сокет.
#             # Если не сделать тут задержку, то второй поток может достаточно долго ждать освобождения сокета.
#             time.sleep(1)
#             with sock_lock:
#                 try:
#                     msg = get_message(sock)
#                     if ACTION in msg and msg[ACTION] == MESSAGE and MESSAGE_TEXT in msg \
#                             and SENDER in msg and DESTINATION in msg and msg[DESTINATION] == self.account_name:
#                         print(f'\nCообщение от {msg[SENDER]}: {msg[MESSAGE_TEXT]}')
#                         log.info(f'Cообщение от {msg[SENDER]}: {msg[MESSAGE_TEXT]}')
#                     else:
#                         log.error(f'Некорректное сообщение с сервера: {msg}')
#                 except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
#                     log.critical(f'Потеряно соединение с сервером')
#                     break
#
#     # Функция - инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера
#     def database_load(self, sock, database, username):
#         # Загружает список известных пользователей
#         try:
#             users_lst = self.user_lst_request(sock, username)
#         except ValueError:
#             log.error('Ошибка запроса списка известных пользователей')
#         else:
#             database.add_known_users(users_lst)
#         # Загружает список контактов
#         try:
#             contacts_lst = self.contacts_lst_request(sock, username)
#         except ValueError:
#             log.error('Ошибка запроса списка контактов')
#         else:
#             for contact in contacts_lst:
#                 database.add_contact(contact)
#
#     def main_func(self):
#         # Запрос имени пользователя, если ранее не задано
#         if not self.account_name:
#             self.account_name = input('Введите имя пользователя: ')
#         try:
#             self.s = socket(self.AF_INET, self.SOCK_STREAM)  # Создает сокет TCP (AF_INET — сетевой, SOCK_STREAM — потоковый)
#             self.s.connect((self.address, self.port))
#
#             msg_to_server = self.create_presence_msg()
#             send_message(self.s, msg_to_server)  # Отправляет на сервер сообщение о присутствии клиента
#
#             server_answer = self.server_response_validator(get_message(self.s))
#             # print(server_answer)    # Код ответа сервера (200/400)
#             log.info(f'Ответ сервера: "{server_answer}"')
#
#         except (ValueError, json.JSONDecodeError):
#             # print('Не удалось декодировать сообщение сервера.')
#             log.error('Не удалось декодировать сообщение сервера')
#         except ConnectionRefusedError:
#             log.critical(f'Нет соединения с сервером {self.address}:{self.port}, отвергнут запрос на подключение')
#             sys.exit(1)
#         else:
#             # Если соединение с сервером установлено корректно, загружаем данные в базу с сервера,
#             # запускаем потоки приёма и отправки сообщений.
#
#             # Основной цикл прогрммы:
#             self.database_load(self.s, self.database, self.account_name)
#             # Поток приёма сообщений
#             recv_thr = threading.Thread(target=self.message_from_server, args=(self.s,))
#             recv_thr.daemon = True
#             recv_thr.start()
#
#             # Поток отправки сообщений и взаимодействие с пользователем.
#             send_thr = threading.Thread(target=self.user_interactive, args=(self.s,))
#             send_thr.daemon = True
#             send_thr.start()
#
#             log.debug('Открыты потоки приёма и отправки сообщений')
#
#             # Справка: Если один из потоков завершён, значит или потеряно соединение или пользователь ввёл exit.
#             # Поскольку все события обработываются в 'демонических' потоках, достаточно просто завершить основной цикл.
#             while True:
#                 time.sleep(1)
#                 if recv_thr.is_alive() and send_thr.is_alive():
#                     continue
#                 break
#
#
# @log_dec
# def main():
#     server_address, server_port, client_name = arg_parser()
#
#     # Инициализация БД
#     database = ClientDbAlchemy(client_name)
#
#     # Экземпляр класса Клиент:
#     client = Client(server_address, server_port, database, client_name)
#     client.main_func()
#
#
# if __name__ == '__main__':
#     main()
