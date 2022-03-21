''' Клиентская программа '''
import os
from logging import getLogger
import argparse
import sys
from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox

from globals.variables import *
from globals.errors import ServerError
from globals.log_decors import log_dec
from client.client_db_alchemy import ClientDbAlchemy
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog

log = getLogger('client')


@log_dec
def arg_parser():
    '''Парсер аргументов командной строки'''
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    if not 1023 < server_port < 65536:
        log.critical(
            f'Ошибка номера порта: {server_port}. '
            f'Допустимы номера с 1024 до 65535')
        exit(1)

    return server_address, server_port, client_name, client_passwd


if __name__ == '__main__':
    '''Запуск основных элементов программы'''
    server_address, server_port, client_name, client_passwd = arg_parser()
    log.debug('Параметры командной строки загружены')
    # Создаём клиентокое приложение
    client_app = QApplication(sys.argv)
    # Если имя пользователя не было указано в командной строке то запросим его
    start_dialog = UserNameDialog()
    if not client_name or not client_passwd:
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и
        # удаляем объект, инааче выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            log.debug(
                f'Using USERNAME = {client_name}, PASSWD = {client_passwd}.')
        else:
            exit(0)
    log.info(
        f'Запущен клиент. Сервер: {server_address}, порт: {server_port}, '
        f'имя пользователя: {client_name}')
    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())
    # !!!keys.publickey().export_key()
    log.debug("Ключи успешно загружены")
    database = ClientDbAlchemy(client_name)
    try:
        transport = ClientTransport(
            server_port,
            server_address,
            database,
            client_name,
            client_passwd,
            keys)
        log.debug("Сокет (транспорт) готов к использованию")
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', error.text)
        exit(1)
    transport.setDaemon = True
    transport.start()
    # Удалим объект диалога за ненадобностью
    del start_dialog
    # Создаём GUI
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()
    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()
