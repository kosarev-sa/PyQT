import os
import sys
from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from datetime import datetime

sys.path.append('../')


class ClientDbAlchemy:
    class KnownUsers:
        def __init__(self, account_name):
            self.id = None
            self.name = account_name

    class MsgHistory:
        def __init__(self, from_user, to_user, message):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.now()

    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact

    def __init__(self, name):
        # Разрешено несколько клиентов одновременно, каждый должен иметь свою БД
        # Клиент мультипоточный, надо отключить проверки на подключения с разных потоков, иначе sqlite3.ProgrammingError
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{name}.db3'
        self.db_engine = create_engine(f'sqlite:///{os.path.join(path, filename)}', echo=False, pool_recycle=7200,
                                       connect_args={'check_same_thread': False})
        self.metadata = MetaData()

        self.known_users_table = Table('known_users', self.metadata,
                                       Column('id', Integer, primary_key=True),
                                       Column('name', String)
                                       )

        self.msg_history_table = Table('message_history', self.metadata,
                                       Column('id', Integer, primary_key=True),
                                       Column('from_user', String),
                                       Column('to_user', String),
                                       Column('message', Text),
                                       Column('date', DateTime)
                                       )

        self.contacts_table = Table('contacts', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('name', String, unique=True)
                                    )

        self.metadata.create_all(self.db_engine)

        mapper(self.KnownUsers, self.known_users_table)
        mapper(self.MsgHistory, self.msg_history_table)
        mapper(self.Contacts, self.contacts_table)

        session = sessionmaker(bind=self.db_engine)
        self.session = session()

        # Очистка таблицы контактов, т.к. при запуске они подгружаются с сервера.
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    # Функция добавления известных пользователей
    def add_known_users(self, users_lst):
        self.session.query(self.KnownUsers).delete()  # Пользователи получаются с сервера, поэтому таблица очищается
        for user in users_lst:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, from_user, to_user, message):
        message_row = self.MsgHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_known_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.name).all()]

    def check_user(self, account_name):
        if self.session.query(self.KnownUsers).filter_by(name=account_name).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_msg_history(self, from_who=None, to_who=None):
        query = self.session.query(self.MsgHistory)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query = query.filter_by(to_user=to_who)
        return [(history_row.from_user, history_row.to_user, history_row.message, history_row.date)
                for history_row in query.all()]


if __name__ == '__main__':  # Отладка
    test_db = ClientDbAlchemy('test1')

    for i in ['test3', 'test4', 'test5']:
        test_db.add_contact(i)
    test_db.add_contact('test4')  # Повторный

    test_db.add_known_users(['test1', 'test2', 'test3', 'test4', 'test5'])

    test_db.save_message('test1', 'test2', f'Тестовое сообщение 1. Время: {datetime.now()}')
    test_db.save_message('test2', 'test1', f'Тестовое сообщение 2. Время: {datetime.now()}!')

    print(test_db.get_contacts())
    print(test_db.get_known_users())

    print(test_db.check_user('test1'))
    print(test_db.check_user('test6'))

    print(test_db.get_msg_history('test2'))
    print(test_db.get_msg_history(to_who='test2'))

    print(test_db.get_msg_history('test3'))

    test_db.del_contact('test4')
    print(test_db.get_contacts())
