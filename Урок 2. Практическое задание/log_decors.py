# Декораторы для дополнительного логирования Серверной и Клиентской программ

import os
import sys
import logging
import traceback
import inspect

from log_config import server_log_config, client_log_config


log = logging.getLogger('client') if 'client' in os.path.split(sys.argv[0])[1] else logging.getLogger('server')
# или:
# log = logging.getLogger('client') if sys.argv[0].find('server') == -1 else logging.getLogger('server')


# Функция-декоратор
def log_dec(func_to_log):
    def log_wrapper(*args, **kwargs):
        return_from_func_to_log = func_to_log(*args, **kwargs)
        log.debug(f'(log_dec) Вызвана функция: {func_to_log.__name__}. Параметры: {args}, {kwargs} \n {" "*71} '
                  f'Модуль вызова: {func_to_log.__module__}. '
                  f'Вызов из функции: {traceback.format_stack()[0].split()[-1]}. '
                  f'Вызов из функции: {inspect.stack()[1][3]}', stacklevel=2)
        return return_from_func_to_log
    return log_wrapper


# Класс-декоратор
class LogDecCls:
    def __call__(self, func_to_log):
        def log_wrapper(*args, **kwargs):
            return_from_func_to_log = func_to_log(*args, **kwargs)
            log.debug(f'(LogDecCls) Вызвана функция: {func_to_log.__name__}. Параметры: {args}, {kwargs} \n {" " * 71} '
                      f'Модуль вызова: {func_to_log.__module__}. '
                      f'Вызов из функции: {traceback.format_stack()[0].split()[-1]}. '
                      f'Вызов из функции: {inspect.stack()[1][3]}', stacklevel=2)
            return return_from_func_to_log
        return log_wrapper
