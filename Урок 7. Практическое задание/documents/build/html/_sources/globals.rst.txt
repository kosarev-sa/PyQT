Globals package
=================================================

Пакет общих утилит, использующихся в разных модулях проекта.

log_decors.py
-------------

.. automodule:: globals.log_decors
   :members:

descriptors_classes.py
----------------------

.. automodule:: globals.descriptors_classes
   :members:

errors.py
---------

.. autoclass:: globals.errors.ServerError
   :members:

metaclasses_verifiers.py
------------------------

.. autoclass:: globals.metaclasses_verifiers.ClientVerifier
   :members:

.. autoclass:: globals.metaclasses_verifiers.ServerVerifier
   :members:

utils.py
--------

globals.utils.get_message(client)

* Функция приёма сообщений от удалённых компьютеров. Принимает сообщения
JSON, декодирует полученное сообщение и проверяет что получен словарь.

globals.utils. **send_message** (sock, message)

* Функция отправки словарей через сокет. Кодирует словарь в формат JSON и
отправляет через сокет.


variables.py
------------

* Содержит глобальные переменные проекта.
