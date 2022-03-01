import sys
import os
from logging.handlers import TimedRotatingFileHandler
from os.path import dirname
from logging import getLogger, Formatter, DEBUG, INFO, StreamHandler


sys.path.append('../')

# Формат лог-записей:
_format = Formatter('%(asctime)-30s %(levelname)-20s %(module)-20s %(message)s')

# Путь к лог-файлу
PATH = dirname(dirname(os.path.abspath(__file__)))
PATH = os.path.join(PATH, 'logs', 'server.log')

# Обработчики вывода
stream_h = StreamHandler(sys.stderr)
stream_h.setFormatter(_format)
stream_h.setLevel(INFO)

file_h = TimedRotatingFileHandler(PATH, when='D', interval=1, encoding='utf8')
file_h.setFormatter(_format)
file_h.setLevel(DEBUG)

# Корневой регистратор
log = getLogger('server')
log.addHandler(stream_h)
log.addHandler(file_h)
log.setLevel(DEBUG)

# Отладка
if __name__ == '__main__':
    log.critical('Критическая ошибка')
    log.error('Ошибка')
    log.warning('Предупреждение')
    log.info('Информационное сообщение')
    log.debug('Отладочная информация')
