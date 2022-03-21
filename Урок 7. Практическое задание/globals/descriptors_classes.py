import sys
from ipaddress import ip_address
from logging import getLogger

from globals.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS
from log_config import server_log_config

log = getLogger('server')


class PortValidator:
    '''Дескриптор порта.'''
    def __set_name__(self, owner, name):
        # owner: <class '__main__.Server'>, name: 'port'
        self.name = name

    def __set__(self, instance, value=DEFAULT_PORT):

        # instance: <__main__.Server object at 0x000000D582740C50>; value: 7777
        if not 1023 < value < 65536:
            log.critical(
                f'exit(1). Номер порта - число от 1024 до 65535. '
                f'Передано: {value}')
            sys.exit(1)
        # Если порт верифицирован, добавляет в список атрибутов экземпляра
        instance.__dict__[self.name] = value


class AddressValidator:
    '''Дескриптор ip-адреса.'''
    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value=DEFAULT_IP_ADDRESS):
        if not value == '':
            try:
                address = ip_address(value)
            except ValueError:
                log.critical(f'exit(1). Неверный IP-адрес. Передано: {value}')
                sys.exit(1)
        # Если ip-адрес верифицирован, добавляет в список атрибутов экземпляра
        instance.__dict__[self.name] = value


if __name__ == '__main__':
    class Test:
        testport = PortValidator()
        testaddr = AddressValidator()

    test = Test()
    test.testport = 65000
    test.testaddr = '1.2.3.a'
    print(test.testport, test.testaddr)
