from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from datetime import datetime

from globals.variables import DATABASE


class ServerDbAlchemy:  # Класс - база данных для сервера
    class Users:        # Класс - таблица всех пользователей. Экземпляр класса - запись в таблице Users
        def __init__(self, account_name):
            self.id = None
            self.name = account_name
            self.last_login = datetime.now()

    class UsersOnline:  # Класс - таблица активных пользователей. Экземпляр класса - запись в таблице UsersOnline
        def __init__(self, user_id, address, port, login_time):
            self.id = None
            self.user = user_id
            self.address = address
            self.port = port
            self.login_time = login_time

    class UsersLoginHistory:  # Класс - таблица истории входов. Экземпляр класса - запись в таблице UsersLoginHistory
        def __init__(self, user_id, date_time, address, port):
            self.id = None
            self.user = user_id
            self.date_time = date_time
            self.address = address
            self.port = port

    def __init__(self):
        # Создание движка базы данных для соединения с СУБД, echo=False - отключаем ведение лога (вывод sql-запросов),
        # pool_recycle=7200 - переустановка соединенияя через 2 часа вместо 8 по умолчанию
        self.db_engine = create_engine(DATABASE, echo=False, pool_recycle=7200)

        self.metadata = MetaData()                        # Объект-каталог MetaData

        self.users_table = Table('users', self.metadata,  # Создание таблицы пользователей
                                 Column('id', Integer, primary_key=True),
                                 Column('name', String, unique=True),
                                 Column('last_login', DateTime)
                                 )

        self.users_online_table = Table('users_online', self.metadata,  # Создание таблицы пользователей онлайн
                                        Column('id', Integer, primary_key=True),
                                        Column('user', ForeignKey('users.id'), unique=True),
                                        Column('address', String),
                                        Column('port', Integer),
                                        Column('login_time', DateTime)
                                        )

        self.users_login_history_table = Table('users_login_history', self.metadata,  # Создание таблицы истории входов
                                               Column('id', Integer, primary_key=True),
                                               Column('user', ForeignKey('users.id')),
                                               Column('date_time', DateTime),
                                               Column('address', String),
                                               Column('port', String)
                                               )

        self.metadata.create_all(self.db_engine)        # Создание таблиц

        # Связи классоов в ORM с таблицами:
        mapper(self.Users, self.users_table)
        mapper(self.UsersOnline, self.users_online_table)
        mapper(self.UsersLoginHistory, self.users_login_history_table)

        session = sessionmaker(bind=self.db_engine)     # Создание сессии
        self.session = session()

        self.session.query(self.UsersOnline).delete()   # При подключении, очищаем таблицу активных пользователей
        self.session.commit()

    def user_login(self, account_name, address, port):  # Функция записывает в базу факт входа (также добавляет
                                                        # пользователя, если новый, обновляет активных)
        print(account_name, address, port)
        check = self.session.query(self.Users).filter_by(name=account_name)  # Проверка на наличие пользователя с именем
        if check.count():                         # Если имя есть:
            user = check.first()
            user.last_login = datetime.now()      # Обновляет время последнего входа
        else:                                     # Если имени нет, создаздаёт нового пользователя:
            user = self.Users(account_name)       # Экземпляр класса self.Users, через который передаёт данные в таблицу
            self.session.add(user)
            self.session.commit()                 # Коммит в т.ч. для присвоения ID

        new_user_online = self.UsersOnline(user.id, address, port, datetime.now())  # Экземпляр класса self.UsersOnline
        self.session.add(new_user_online)         # Запись в таблицу активных пользователей

        history = self.UsersLoginHistory(user.id, datetime.now(), address, port)  # Экз-р класса self.UsersLoginHistory
        self.session.add(history)                 # Запись в таблицу активных пользователей

        self.session.commit()                     # Коммитит (сохраняет/применяет) изменения

    def user_logout(self, account_name):          # Функция фиксирует отключение пользователя
        user = self.session.query(self.Users).filter_by(name=account_name).first()  # Запрашивает отключающегося

        self.session.query(self.UsersOnline).filter_by(user=user.id).delete()      # Удаляет из таблицы активных(онлайн)

        self.session.commit()                     # Коммитит (сохраняет/применяет) изменения

    def users_lst(self):  # Функция возвращает список кортежей всех известных пользователей со временем последнего входа
        return self.session.query(self.Users.name,
                                  self.Users.last_login,
                                  ).all()

    def active_users_lst(self):                   # Функция возвращает список кортежей активных пользователей
        return self.session.query(self.Users.name,
                                  self.UsersOnline.address,
                                  self.UsersOnline.port,
                                  self.UsersOnline.login_time,
                                  ).join(self.Users).all()

    def login_history(self, account_name=None):  # Функция возвращает историю входов пользователя или всех пользователей
        login_history_query = self.session.query(self.Users.name,
                                                 self.UsersLoginHistory.date_time,
                                                 self.UsersLoginHistory.address,
                                                 self.UsersLoginHistory.port,
                                                 ).join(self.Users)
        if account_name:                         # Если указано имя, фильтруем по нему:
            login_history_query = login_history_query.filter(self.Users.name == account_name)
        return login_history_query.all()


if __name__ == '__main__':                                  # Отладка
    test_db = ServerDbAlchemy()
    test_db.user_login('client_1', '192.168.1.2', 7777)     # 'Подключение' пользователя
    test_db.user_login('client_2', '192.168.1.3', 8888)     # 'Подключение' пользователя
    test_db.user_login('client_3', '192.168.1.4', 9999)     # 'Подключение' пользователя
    print(test_db.active_users_lst())                       # Список кортежей - активных пользователей

    test_db.user_logout('client_1')                         # 'Отключение' пользователя
    print(test_db.active_users_lst())                       # Список кортежей активных пользователей

    print(test_db.login_history('client_1'))                # Запрос истории входов пользователя client_1
    print(test_db.users_lst())                              # Список известных пользователей
