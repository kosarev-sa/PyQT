# Servers unittest

import unittest
from globals.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from server import client_message_validator


class TestServerFunction(unittest.TestCase):
    def setUp(self):
        self.tests_time = 1.12345
        self.response_ok = {RESPONSE: 200}
        self.response_error = {RESPONSE: 400, ERROR: 'Bad Request'}
        self.msg_from_client = {ACTION: PRESENCE,
                                TIME: self.tests_time,
                                USER:
                                    {ACCOUNT_NAME: 'Guest'}
                                }
        self.msg_from_client_without_action = {TIME: self.tests_time,
                                               USER:
                                                   {ACCOUNT_NAME: 'Guest'}
                                               }
        self.msg_from_client_with_wrong_action = {ACTION: 'run',
                                                  TIME: self.tests_time,
                                                  USER:
                                                      {ACCOUNT_NAME: 'Guest'}
                                                  }
        self.msg_from_client_without_time = {ACTION: PRESENCE,
                                             USER:
                                                 {ACCOUNT_NAME: 'Guest'}
                                             }
        self.msg_from_client_without_user = {ACTION: PRESENCE,
                                             TIME: self.tests_time,
                                             }
        self.msg_with_unknown_account_name = {ACTION: PRESENCE,
                                              TIME: self.tests_time,
                                              USER:
                                                  {ACCOUNT_NAME: 'New_Name'}
                                              }

    def test_msg_without_action(self):
        self.assertEqual(client_message_validator(self.msg_from_client_without_action), self.response_error)

    def test_msg_with_wrong_action(self):
        self.assertEqual(client_message_validator(self.msg_from_client_with_wrong_action), self.response_error)

    def test_msg_without_time(self):
        self.assertEqual(client_message_validator(self.msg_from_client_without_time), self.response_error)

    def test_msg_without_user(self):
        self.assertEqual(client_message_validator(self.msg_from_client_without_user), self.response_error)

    def test_msg_with_unknown_account_name(self):
        self.assertEqual(client_message_validator(self.msg_with_unknown_account_name), self.response_error)

    def test_ok_msg(self):
        self.assertEqual(client_message_validator(self.msg_from_client), self.response_ok)

    def tearDown(self) -> None:
        pass


if __name__ == '__main__':
    unittest.main()
