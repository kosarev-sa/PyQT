Client programm module
=================================================

Клиентское приложение для обмена сообщениями. Поддерживает
отправку сообщений пользователям которые находятся в сети, сообщения шифруются
с помощью алгоритма RSA с длинной ключа 2048 bit.

Поддерживает аргументы коммандной строки:

``python client_main.py {имя сервера} {порт} -n или --name {имя
пользователя} -p или --password {пароль}``

#. {имя сервера} - адрес сервера сообщений.
#. {порт} - порт по которому принимаются подключения
#. -n или --name - имя пользователя с которым произойдёт вход в систему.
#. -p или --password - пароль пользователя.

Все опции командной строки являются необязательными, но имя пользователя и
пароль необходимо использовать в паре.

Примеры использования:

* ``python client.py``

*Запуск приложения с параметрами по умолчанию.*

* ``python client_main.py ip_address some_port``

*Запуск приложения с указанием подключаться к серверу по адресу ip_address:port*

* ``python -n client_1 -p 124``

*Запуск приложения с пользователем client_1 и паролем 124*

* ``python client_main.py ip_address some_port -n client_1 -p 124``

*Запуск приложения с пользователем client_1 и паролем 124 и указанием
подключаться к серверу по адресу ip_address:port*

client_main.py
--------------

Запускаемый модуль, содержит парсер аргументов командной строки и функционал
инициализации приложения.

**client_main.arg_parser()**
    Парсер аргументов командной строки возвращает кортеж из 4 элементов:

	* адрес сервера
	* порт
	* имя пользователя
	* пароль

    Выполняет проверку на корректность номера порта.


client_db_alchemy.py
--------------------

.. autoclass:: client.client_db_alchemy.ClientDbAlchemy
	:members:

transport.py
------------

.. autoclass:: client.transport.ClientTransport
	:members:

main_window.py
--------------

.. autoclass:: client.main_window.ClientMainWindow
	:members:

start_dialog.py
---------------

.. autoclass:: client.start_dialog.UserNameDialog
	:members:


add_contact.py
--------------

.. autoclass:: client.add_contact.AddContactDialog
	:members:


del_contact.py
--------------

.. autoclass:: client.del_contact.DelContactDialog
	:members:
