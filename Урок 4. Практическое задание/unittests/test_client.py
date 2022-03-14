# Clients unittest

import unittest
from globals.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from client import create_presence_msg, server_response_validator


class TestClientsFunctions(unittest.TestCase):
    def setUp(self):
        self.tests_time = 1.12345
        self.wait_presence_msg = {ACTION: PRESENCE,
                                  TIME: self.tests_time,
                                  USER:
                                      {ACCOUNT_NAME: 'Guest'}
                                  }

        self.msg_from_server_200 = {RESPONSE: 200}
        self.wait_ok_ans = '200 : OK'

        self.msg_from_server_400 = {RESPONSE: 400, ERROR: 'Bad Request'}
        self.wait_bad_request_ans = '400 : Bad Request'

        self.msg_from_server_without_response = {ERROR: 'Bad Request'}

    def test_create_presence_msg(self):
        test = create_presence_msg()
        test[TIME] = 1.12345
        self.assertEqual(test, self.wait_presence_msg)

    def test_ok_server_response(self):
        self.assertEqual(server_response_validator(self.msg_from_server_200), self.wait_ok_ans)

    def test_error_server_response(self):
        self.assertEqual(server_response_validator(self.msg_from_server_400), self.wait_bad_request_ans)

    def test_msg_without_response(self):
        self.assertRaises(ValueError, server_response_validator, self.msg_from_server_without_response)

    def tearDown(self) -> None:
        pass


if __name__ == '__main__':
    unittest.main()
