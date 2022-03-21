''' Серверная программа '''
import configparser
import os
import sys
from logging import getLogger
import argparse
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from globals.variables import DEFAULT_PORT
from globals.log_decors import LogDecCls
from server.main_window import MainWindow
from server.server_db_alchemy import ServerDbAlchemy
from server.core import Server

log = getLogger('server')


@LogDecCls()
def arg_parser(default_port, default_address):
    '''Парсер аргументов командной строки'''
    log.debug(
        f'Инициализация парсера аргументов коммандной строки: {sys.argv}')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    gui_flag = namespace.no_gui
    log.debug('Аргументы успешно загружены')
    return listen_address, listen_port, gui_flag


@LogDecCls()
def config_load():
    '''Настройки'''
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


@LogDecCls()
def main():
    ''' Функция запуска основных элементов программы '''
    config = config_load()
    listen_address, listen_port, gui_flag = arg_parser(
        config['SETTINGS']['Default_port'],
        config['SETTINGS']['Listen_Address'])
    database = ServerDbAlchemy(os.path.join(
        config['SETTINGS']['Database_path'],
        config['SETTINGS']['Database_file']))

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    if gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера.')
            if command == 'exit':
                server.running = False
                server.join()
                break
    # Если не указан запуск без GUI, то запускаем GUI:
    else:
        # Создаём графическое окуружение для сервера:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)
        # Запускаем GUI
        server_app.exec_()
        # По закрытию окон останавливаем обработчик сообщений
        server.running = False


if __name__ == '__main__':
    main()
