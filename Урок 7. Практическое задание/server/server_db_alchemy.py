from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime, Text
from sqlalchemy.orm import mapper, sessionmaker
from datetime import datetime

from globals.variables import DATABASE


class ServerDbAlchemy:
    '''Класс - база данных для сервера.'''
    class Users:
        '''Класс - таблица всех пользователей.
        Экземпляр класса - запись в таблице Users.'''
        def __init__(self, account_name, passwd_hash):
            self.id = None
            self.name = account_name
            self.passwd_hash = passwd_hash
            self.pubkey = None
            self.last_login = datetime.now()

    class UsersOnline:
        '''Класс - таблица активных пользователей.
        Экземпляр класса - запись в таблице UsersOnline.'''
        def __init__(self, user_id, address, port, login_time):
            self.id = None
            self.user = user_id
            self.address = address
            self.port = port
            self.login_time = login_time

    class UsersLoginHistory:
        '''Класс - таблица истории входов.
        Экземпляр класса - запись в таблице UsersLoginHistory.'''
        def __init__(self, user_id, date_time, address, port):
            self.id = None
            self.user = user_id
            self.date_time = date_time
            self.address = address
            self.port = port

    class UsersContacts:
        '''Класс - таблица контактов пользователей.
        Экземпляр класса - запись в таблице UsersContacts.'''
        def __init__(self, user_id, contact_id):
            self.id = None
            self.user = user_id
            self.contact = contact_id

    class UsersMsgHistory:
        '''Класс - таблица истории действий.
        Экземпляр класса - запись в таблице UsersMsgHistory.'''
        def __init__(self, user_id):
            self.id = None
            self.user = user_id
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        '''
        Создание движка базы данных для соединения с СУБД,echo=False -
        отключаем ведение лога (вывод sql-запросов), pool_recycle=7200 -
        переустановка соединенияя через 2 часа вместо 8 по умолчанию
        self.db_engine = create_engine(DATABASE, echo=False,
        pool_recycle=7200)
        '''
        print(path)
        self.db_engine = create_engine(
            f'sqlite:///{path}',
            echo=False,
            pool_recycle=7200,
            connect_args={
                'check_same_thread': False})

        self.metadata = MetaData()
        # Объект-каталог MetaData

        self.users_table = Table('users', self.metadata,
                                 # Создание таблицы пользователей
                                 Column('id', Integer, primary_key=True),
                                 Column('name', String, unique=True),
                                 Column('passwd_hash', String),
                                 Column('pubkey', Text),
                                 Column('last_login', DateTime)
                                 )

        self.users_online_table = Table('users_online', self.metadata,
                                        # Создание таблицы пользователей онлайн
                                        Column(
                                            'id', Integer, primary_key=True),
                                        Column(
                                            'user', ForeignKey('users.id'), unique=True),
                                        Column('address', String),
                                        Column('port', Integer),
                                        Column('login_time', DateTime)
                                        )

        self.users_login_history_table = Table('users_login_history',
                                               self.metadata,
                                               # Создание таблицы истории входов
                                               Column(
                                                   'id', Integer, primary_key=True),
                                               Column(
                                                   'user', ForeignKey('users.id')),
                                               Column('date_time', DateTime),
                                               Column('address', String),
                                               Column('port', String)
                                               )

        self.users_contacts_table = Table('users_contacts', self.metadata,
                                          # Создание таблицы контактов пользователей
                                          Column(
                                              'id', Integer, primary_key=True),
                                          Column(
                                              'user', ForeignKey('users.id')),
                                          Column(
                                              'contact', ForeignKey('users.id'))
                                          )

        self.users_msg_history_table = Table('users_msg_history', self.metadata,
                                             # Создание таблицы истории сообщений
                                             Column(
                                                 'id', Integer, primary_key=True),
                                             Column(
                                                 'user', ForeignKey('users.id')),
                                             Column('sent', Integer),
                                             Column('accepted', Integer)
                                             )

        self.metadata.create_all(self.db_engine)
        # Создание таблиц
        # Связи классоов в ORM с таблицами:
        mapper(self.Users, self.users_table)
        mapper(self.UsersOnline, self.users_online_table)
        mapper(self.UsersLoginHistory, self.users_login_history_table)
        mapper(self.UsersContacts, self.users_contacts_table)
        mapper(self.UsersMsgHistory, self.users_msg_history_table)

        session = sessionmaker(bind=self.db_engine)     # Создание сессии
        self.session = session()

        # При подключении, очищаем таблицу активных пользователей
        self.session.query(self.UsersOnline).delete()
        self.session.commit()

    def user_login(self, account_name, address, port, key):
        '''Метод, выполняющийся при входе пользователя,
        записывает в базу факт входа.
        Обновляет открытый ключ пользователя при его изменении.'''
        # Запрос в таблицу пользователей на наличие там пользователя с таким
        # именем.
        query = self.session.query(self.Users).filter_by(name=account_name)
        # Если имя уже присутствует в таблице,
        # обновляем время последнего входа и проверяем корректность ключа.
        # Если клиент прислал новый ключ,сохраняем его.
        if query.count():
            user = query.first()
            user.last_login = datetime.now()
            if user.pubkey != key:
                user.pubkey = key
        # Если нет, то генерируем исключение.
        else:
            raise ValueError('Пользователь не зарегистрирован.')

        # Теперь можно создать запись в таблицу активных пользователей о факте
        # входа.
        new_active_user = self.UsersOnline(
            user.id, address, port, datetime.now())
        self.session.add(new_active_user)

        # и сохранить в историю входов
        history = self.UsersLoginHistory(
            user.id, datetime.now(), address, port)
        self.session.add(history)

        self.session.commit()

    def add_user(self, name, passwd_hash):
        '''Метод регистрации пользователя. Принимает имя и хэш пароля, создаёт
        запись в таблице статистики.'''
        user_row = self.Users(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.UsersMsgHistory(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        '''Метод, удаляющий пользователя из базы.'''
        user = self.session.query(self.Users).filter_by(name=name).first()
        self.session.query(self.UsersOnline).filter_by(user=user.id).delete()
        self.session.query(
            self.UsersLoginHistory).filter_by(
            user=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(user=user.id).delete()
        self.session.query(
            self.UsersContacts).filter_by(
            contact=user.id).delete()
        self.session.query(
            self.UsersMsgHistory).filter_by(
            user=user.id).delete()
        self.session.query(self.Users).filter_by(name=name).delete()
        self.session.commit()

    def get_hash(self, name):
        '''Метод получения хэша пароля пользователя.'''
        user = self.session.query(self.Users).filter_by(name=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        '''Метод получения публичного ключа пользователя.'''
        user = self.session.query(self.Users).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        '''Метод проверяющий существование пользователя.'''
        if self.session.query(self.Users).filter_by(name=name).count():
            return True
        else:
            return False

    def user_logout(self, account_name):
        '''Функция фиксирует отключение пользователя.'''
        user = self.session.query(self.Users).filter_by(
            name=account_name).first()  # Запрашивает отключающегося

        self.session.query(self.UsersOnline).filter_by(
            user=user.id).delete()      # Удаляет из таблицы активных(онлайн)

        self.session.commit()        # Коммитит (сохраняет/применяет) изменения

    def msg_counter(self, sender, recipient):
        '''Функция фиксирует передачу сообщения и увеличивает счетчики в БД.'''
        sender_id = self.session.query(self.Users).filter_by(
            name=sender).first().id        # Получает ID отправителя
        recipient_id = self.session.query(self.Users).filter_by(
            name=recipient).first().id  # Получает ID получателя

        sender_data_row = self.session.query(
            self.UsersMsgHistory).filter_by(
            user=sender_id).first()    # Cтрока истории
        sender_data_row.sent += 1             # Увеличивает счётчик отправителя
        recipient_data_row = self.session.query(
            self.UsersMsgHistory).filter_by(
            user=recipient_id).first()   # Cтр. ист.
        recipient_data_row.accepted += 1       # Увеличивает счётчик получателя

        self.session.commit()

    def add_contact(self, account_name, contact_name):
        '''Функция добавляет контакт для пользователя.'''
        user = self.session.query(self.Users).filter_by(
            name=account_name).first()      # Получает пользователя
        contact = self.session.query(self.Users).filter_by(
            name=contact_name).first()   # Получает контакт
        # Проверяет, что контакт может существовать и что не дубль:
        if not contact or self.session.query(
                self.UsersContacts).filter_by(
                user=user.id,
                contact=contact.id).count():
            return
        contact_data_row = self.UsersContacts(
            user.id, contact.id)                      # Создаёт объект
        # Заносит его в базу
        self.session.add(contact_data_row)
        self.session.commit()

    def remove_contact(self, account_name, contact_name):
        '''Функция удаляет контакт из базы данных.'''
        user = self.session.query(self.Users).filter_by(
            name=account_name).first()      # Получает пользователя
        contact = self.session.query(self.Users).filter_by(
            name=contact_name).first()   # Получает контакт
        # Проверяет что контакт может существовать (полю пользователь мы
        # доверяем)
        if not contact:
            return
        print(self.session.query(self.UsersContacts)
              .filter(self.UsersContacts.user == user.id, self.UsersContacts.contact == contact.id)
              .delete()                     # Находит и удаляет контакт
              )
        self.session.commit()

    def users_lst(self):
        '''Функция возвращает список кортежей всех известных пользователей
        со временем последнего входа.'''
        return self.session.query(self.Users.name,
                                  self.Users.last_login,
                                  ).all()

    def active_users_lst(self):
        '''Функция возвращает список кортежей активных пользователей.'''
        return self.session.query(self.Users.name,
                                  self.UsersOnline.address,
                                  self.UsersOnline.port,
                                  self.UsersOnline.login_time,
                                  ).join(self.Users).all()

    def login_history(self, account_name=None):
        '''Функция возвращает историю входов пользователя или всех
        пользователей.'''
        login_history_query = self.session.query(
            self.Users.name,
            self.UsersLoginHistory.date_time,
            self.UsersLoginHistory.address,
            self.UsersLoginHistory.port,
        ).join(
            self.Users)
        if account_name:                 # Если указано имя, фильтруем по нему:
            login_history_query = login_history_query.filter(
                self.Users.name == account_name)
        return login_history_query.all()

    def get_contacts(self, account_name):
        '''Функция возвращает список контактов пользователя.'''
        user = self.session.query(self.Users).filter_by(
            name=account_name).one()        # Получает пользователя
        query = self.session.query(
            self.UsersContacts,
            self.Users.name).filter_by(
            user=user.id) .join(
            self.Users,
            self.UsersContacts.contact == self.Users.id)
            # Запрашивает список контактов
        # Выбирает только имена пользователей и возвращает их список
        return [contact[1] for contact in query.all()]


    def msg_history(self):
        '''Функция возвращает количество переданных и полученных сообщений.'''
        query = self.session.query(
            self.Users.name,
            self.Users.last_login,
            self.UsersMsgHistory.sent,
            self.UsersMsgHistory.accepted) .join(
            self.Users)
        return query.all()                  # Возвращает список кортежей


# if __name__ == '__main__':                                  # Отладка
#     test_db = ServerDbAlchemy()
#     test_db.user_login('client_1', '192.168.1.2', 7777)     # 'Подключение' пользователя
#     test_db.user_login('client_2', '192.168.1.3', 8888)     # 'Подключение' пользователя
#     test_db.user_login('client_3', '192.168.1.4', 9999)     # 'Подключение' пользователя
#     print(test_db.active_users_lst())                       # Список кортежей - активных пользователей
#
#     test_db.user_logout('client_1')                         # 'Отключение' пользователя
#     print(test_db.active_users_lst())                       # Список кортежей активных пользователей
#
#     print(test_db.login_history('client_1'))                # Запрос истории входов пользователя client_1
#     print(test_db.users_lst())                              # Список известных пользователей
#
#     test_db.add_contact('client_1', 'client_2')             # Добавляем контакт для client_1
#     test_db.add_contact('client_1', 'client_3')             # Добавляем контакт для client_1
#     test_db.add_contact('client_1', 'client_4')             # Пытаемся добавить несуществующий контакт для client_1
#     test_db.remove_contact('client_1', 'client_2')          # Удаляем контакт client_2 из списка пользователя client_1
#     print(test_db.get_contacts('client_1'))                 # ['client_3'] - список контактов пользователя client_1
#
#     test_db.msg_counter('client_1', 'client_3')             # Пользователь client_1 отправил сообщение client_3
#     print(test_db.msg_history())                            # Проверяем
# отображение истории числа сообщений
