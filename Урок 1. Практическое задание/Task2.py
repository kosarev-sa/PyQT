# Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
# Меняться должен только последний октет каждого адреса.
# По результатам проверки должно выводиться соответствующее сообщение.

from pprint import pprint

from Task1 import host_ping, checked_ip


def host_range_ping(ip_lst):   # Перебирает последующие n ip-адресов после заданного
    for_check_ip_lst = []
    n = int(input('Введите число последующих ip-адресов для проверки доступности: '))
    for ip in ip_lst:
        for i in range(1, n + 1):
            ip_last_num = int(str(ip).split('.')[-1])
            if ip_last_num < 255:
                ip = ip + 1
                for_check_ip_lst.append(ip)
    return for_check_ip_lst


ip_range = []
try:
    ip_range.extend(host_range_ping(checked_ip['reached'])).extend(host_range_ping(checked_ip['reachless']))
except AttributeError:
    pass
checked_ip = host_ping(ip_range)
pprint(checked_ip)

# 192.168.0.1: Узел доступен
# 192.168.1.255: Узел недоступен
# 80.0.1.1: Узел доступен
# 77.88.55.80: Узел доступен
# 94.100.180.200: Узел доступен
# {'reached': [IPv4Address('192.168.0.1'),
#              IPv4Address('80.0.1.1'),
#              IPv4Address('77.88.55.80'),
#              IPv4Address('94.100.180.200')],
#  'reachless': [IPv4Address('192.168.1.255')]}
# Введите число последующих ip-адресов для проверки доступности: 3
# 192.168.0.2: Узел доступен
# 192.168.0.3: Узел доступен
# 192.168.0.4: Узел доступен
# 80.0.1.2: Узел доступен
# 80.0.1.3: Узел доступен
# 80.0.1.4: Узел доступен
# 77.88.55.81: Узел недоступен
# 77.88.55.82: Узел недоступен
# 77.88.55.83: Узел недоступен
# 94.100.180.201: Узел доступен
# 94.100.180.202: Узел доступен
# 94.100.180.203: Узел доступен
# {'reached': [IPv4Address('192.168.0.2'),
#              IPv4Address('192.168.0.3'),
#              IPv4Address('192.168.0.4'),
#              IPv4Address('80.0.1.2'),
#              IPv4Address('80.0.1.3'),
#              IPv4Address('80.0.1.4'),
#              IPv4Address('94.100.180.201'),
#              IPv4Address('94.100.180.202'),
#              IPv4Address('94.100.180.203')],
#  'reachless': [IPv4Address('77.88.55.81'),
#                IPv4Address('77.88.55.82'),
#                IPv4Address('77.88.55.83')]}
