# Лаунчер. Запуск тестовых Сервера и Клиентов с отдельными консолями

import subprocess

PROCESS = []

while True:
    ACTION = input('Выберите действие: q - выход, s - запустить сервер и клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        break

    elif ACTION == 's':
        PROCESS.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(3):
            PROCESS.append(subprocess.Popen(f'python client.py -n client_{i+1}',
                                            creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif ACTION == 'x':
        while PROCESS:
            closing_process = PROCESS.pop()
            closing_process.kill()
