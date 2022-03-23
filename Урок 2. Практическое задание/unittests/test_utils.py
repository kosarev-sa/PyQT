# Utils unittest (тесты универсальных функций)

import unittest
import json

from globals.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, ENCODING
from globals.utils import get_message, send_message


class SocketExample:
    def __init__(self, dct_example):
        self.test_dct = dct_example
        self.encoded_message = None
        self.receved_message = None

    def send(self, msg_for_send):
        # Тестовая функция отправки кодирует сообщение и сохраняет что должно было отправлено в сокет
        js_msg = json.dumps(self.test_dct)
        self.encoded_message = js_msg.encode(ENCODING)
        self.receved_message = msg_for_send

    def recv(self, max_size):
        # Получаем данные из сокета -> json-строку -> возвращаем сообщение в байтах
        js_msg = json.dumps(self.test_dct)
        return js_msg.encode(ENCODING)


class TestUtilsFunctions(unittest.TestCase):
    def setUp(self) -> None:
        self.tests_time = 1.12345
        self.sending_msg = {ACTION: PRESENCE,
                            TIME: self.tests_time,
                            USER:
                                {ACCOUNT_NAME: 'test'}
                            }
        self.msg_from_server_200 = {RESPONSE: 200}
        self.msg_from_server_400 = {RESPONSE: 400, ERROR: 'Bad Request'}

    def test_send_message(self):
        # тестовый сокет хранит тестовый словарь
        test_socket = SocketExample(self.sending_msg)
        # тестируем функцию отправки сообщения, результат сохраняем в тестовом сокете
        send_message(test_socket, self.sending_msg)
        # проверка результата кодирования и результата тестируемой функции
        self.assertEqual(test_socket.encoded_message, test_socket.receved_message)
        # +проверка генерации исключения, если передан не словарь
        with self.assertRaises(Exception):
            send_message(test_socket, test_socket)

    def test_get_message(self):
        # тестируем функцию приема сообщения
        # создаем сокеты и передаем сообщения сервера с ответом ok/error
        test_socket_200 = SocketExample(self.msg_from_server_200)
        test_socket_400 = SocketExample(self.msg_from_server_400)
        # проверяем правильность расшифровки словаря
        self.assertEqual(get_message(test_socket_200), self.msg_from_server_200)
        self.assertEqual(get_message(test_socket_400), self.msg_from_server_400)

    def tearDown(self) -> None:
        pass


if __name__ == '__main__':
    unittest.main()
