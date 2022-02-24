# Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
# Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
# В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
# («Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().

from ipaddress import ip_address
from socket import gethostbyname
from subprocess import check_call, PIPE, CalledProcessError
from pprint import pprint


def host_ping(netnode_lst):
    reach_of_netnodes = {'reached': [],
                         'reachless': []
                         }
    for netnode in netnode_lst:
        try:
            netnode_ip = ip_address(netnode)
        except ValueError:
            netnode_ip = ip_address(gethostbyname(netnode))

        try:
            check_call(f'ping {netnode_ip}', stdout=PIPE)
            print(f'{netnode_ip}: Узел доступен')
            reach_of_netnodes['reached'].append(netnode_ip)
        except CalledProcessError:
            print(f'{netnode_ip}: Узел недоступен')
            reach_of_netnodes['reachless'].append(netnode_ip)
    return reach_of_netnodes


nodes_lst = ['192.168.0.1', '192.168.1.255', '80.0.1.1', 'yandex.ru', 'mail.ru']
checked_ip = host_ping(nodes_lst)
pprint(checked_ip)

# 192.168.0.1: Узел доступен
# 192.168.1.255: Узел недоступен
# 80.0.1.1: Узел доступен
# 77.88.55.55: Узел доступен
# 94.100.180.201: Узел доступен
# {'reached': [IPv4Address('192.168.0.1'),
#              IPv4Address('80.0.1.1'),
#              IPv4Address('77.88.55.55'),
#              IPv4Address('94.100.180.201')],
#  'reachless': [IPv4Address('192.168.1.255')]}
