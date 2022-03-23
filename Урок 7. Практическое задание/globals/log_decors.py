# Декораторы для дополнительного логирования Серверной и Клиентской программ

import os
import sys
import logging
import traceback
import inspect
from socket import socket

from log_config import server_log_config, client_log_config


log = logging.getLogger('client') \
    if 'client' in os.path.split(sys.argv[0])[
    1] else logging.getLogger('server')
# или:
# log = logging.getLogger('client') if sys.argv[0].find('server') == -1 else logging.getLogger('server')


# Функция-декоратор
def log_dec(func_to_log):
    '''Декоратор, выполняющий логирование вызовов функций. Сохраняет события
    типа debug, содержащие информацию о имени вызываемой функиции, параметры
    с которыми вызывается функция, и модуль, вызывающий функцию.'''
    def log_wrapper(*args, **kwargs):
        return_from_func_to_log = func_to_log(*args, **kwargs)
        log.debug(
            f'(log_dec) Вызвана функция: {func_to_log.__name__}. '
            f'Параметры: {args}, {kwargs} \n {" "*71} '
            f'Модуль вызова: {func_to_log.__module__}. '
            f'Вызов из функции: {traceback.format_stack()[0].split()[-1]}. '
            f'Вызов из функции: {inspect.stack()[1][3]}', stacklevel=2)
        return return_from_func_to_log
    return log_wrapper


class LogDecCls:
    '''Класс-декоратор.'''

    def __call__(self, func_to_log):
        def log_wrapper(*args, **kwargs):
            return_from_func_to_log = func_to_log(*args, **kwargs)
            log.debug(
                f'(LogDecCls) Вызвана функция: {func_to_log.__name__}. '
                f'Параметры: {args}, {kwargs} \n {" " * 71} '
                f'Модуль вызова: {func_to_log.__module__}. '
                f'Вызов из функции: {traceback.format_stack()[0].split()[-1]}. '
                f'Вызов из функции: {inspect.stack()[1][3]}', stacklevel=2)
            return return_from_func_to_log
        return log_wrapper


def login_required(func):
    '''
    Декоратор, проверяющий, что клиент авторизован на сервере.
    Проверяет, что передаваемый объект сокета находится в
    списке авторизованных клиентов.
    За исключением передачи словаря-запроса
    на авторизацию. Если клиент не авторизован,
    генерирует исключение TypeError
    '''

    def checker(*args, **kwargs):
        # проверяем, что первый аргумент - экземпляр Server
        # Импортить необходимо тут, иначе ошибка рекурсивного импорта
        from server.core import Server
        from globals.variables import ACTION, PRESENCE
        if isinstance(args[0], Server):
            found = False
            for arg in args:
                if isinstance(arg, socket):
                    # Проверяем, что данный сокет есть в списке users_names
                    # класса Server
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            # Теперь надо проверить, что передаваемые аргументы не presence
            # сообщение. Если presense, то разрешаем
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            # Если не не авторизован и не сообщение начала авторизации, то
            # вызываем исключение
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker
