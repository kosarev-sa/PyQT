# Универсальные функции

import json
from globals.variables import MAX_MSG_SIZE, ENCODING


def get_message(client):
    # Функция принимает байты <= MAX_MSG_SIZE
    encoded_response = client.recv(MAX_MSG_SIZE)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)

        # Выдаёт словарь
        if isinstance(response, dict):
            return response

        # Если принят не словарь, отдаёт ошибку значения
        raise ValueError
    raise ValueError


def send_message(sock, msg):
    # Функция принимает словарь
    js_msg = json.dumps(msg)

    # Кодирует
    encoded_message = js_msg.encode(ENCODING)

    # Отправляет его в сообщении
    sock.send(encoded_message)
