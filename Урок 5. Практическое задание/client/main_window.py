from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication, QListView
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, QEvent, Qt
import sys
import json
from logging import getLogger

from client.client_ui_conv import Ui_MainClientWindow
from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog
from client.client_db_alchemy import ClientDbAlchemy
from client.transport import ClientTransport
from client.start_dialog import UserNameDialog
from globals.errors import ServerError

sys.path.append('../')

log = getLogger('client')


class ClientMainWindow(QMainWindow):
    def __init__(self, database, transport):
        super().__init__()

        self.db = database
        self.s = transport

        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        # "Выход"
        self.ui.menu_exit.triggered.connect(qApp.exit)

        # "Отправить сообщение"
        self.ui.btn_send.clicked.connect(self.send_message)

        # "Добавить контакт"
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        # Удалить контакт
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        # Дополнительные требующиеся атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        # Даблклик по листу контактов отправляется в обработчик
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    # Деактивировать поля ввода
    def set_disabled_input(self):
        # Надпись  - получатель
        self.ui.label_new_message.setText('Выберите получателя в окне контактов двойным кликом мыши.')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        # Поле ввода и кнопка отправки неактивны до выбора получателя
        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

    # Заполняем историю сообщений
    def history_list_update(self):
        # Получаем историю сортированную по дате
        lst = sorted(self.db.get_msg_history(self.current_chat), key=lambda item: item[3])
        # Если модель не создана, создадим
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        # Очистим от старых записей
        self.history_model.clear()
        # Берём не более 20 последних записей
        length = len(lst)
        start_index = 0
        if length > 20:
            start_index = length - 20
        # Заполнение модели записями, так же стоит разделить входящие и исходящие, выделяем их разным фоном.
        # Записи в обратном порядке, поэтому выбираем их с конца и не более 20.
        for i in range(start_index, length):
            item = lst[i]
            if item[1] == 'in':
                mess = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    # Функция обработчик даблклика по контакту
    def select_active_user(self):
        # Выбранный пользователем (даблклик) находится в выделеном элементе в QListView
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        # Вызываем основную функцию
        self.set_active_user()

    # Функция устанавливающая активного собеседника
    def set_active_user(self):
        # Ставим надпись и активируем кнопки
        self.ui.label_new_message.setText(f'Ввод сообщенние для {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)

        # Заполняем окно историю сообщений по требуемому пользователю
        self.history_list_update()

    # Функция обновляющая контакт-лист
    def clients_list_update(self):
        contacts_lst = self.db.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_lst):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    # Функция добавления контакта
    def add_contact_window(self):
        global select_dialog
        select_dialog = AddContactDialog(self.s, self.db)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    # Функция - обработчик добавления, сообщает серверу, обновляет таблицу и список контактов
    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    # Функция добавляющяя контакт в базы
    def add_contact(self, new_contact):
        try:
            self.s.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.db.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            log.info(f'Успешно добавлен контакт {new_contact}')
            self.messages.information(self, 'Успех', 'Контакт успешно добавлен.')

    # Функция удаления контакта
    def delete_contact_window(self):
        global remove_dialog
        remove_dialog = DelContactDialog(self.db)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    # Функция обработчик удаления контакта, сообщает на сервер, обновляет таблицу контактов
    def delete_contact(self, item):
        selected = item.selector.currentText()
        try:
            self.s.remove_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.db.del_contact(selected)
            self.clients_list_update()
            log.info(f'Успешно удалён контакт {selected}')
            self.messages.information(self, 'Успех', 'Контакт успешно удалён.')
            item.close()
            # Если удалён активный пользователь, то деактивируем поля ввода
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    # Функция отправки собщения пользователю
    def send_message(self):
        # Текст в поле. Проверяем что поле не пустое, затем забирается сообщение и поле очищается
        msg_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not msg_text:
            return
        try:
            self.s.create_send_message(self.current_chat, msg_text)
            pass
        except ServerError as err:
            self.messages.critical(self, 'Ошибка', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.db.save_message(self.current_chat, 'out', msg_text)
            log.debug(f'Отправлено сообщение для {self.current_chat}: {msg_text}')
            self.history_list_update()

    # Слот приёма нового сообщений
    @pyqtSlot(str)
    def message(self, sender):
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # Проверим есть ли такой пользователь у нас в контактах:
            if self.db.check_contact(sender):
                # Если есть, спрашиваем о желании открыть с ним чат и открываем при желании
                if self.messages.question(self, 'Новое сообщение', f'Получено новое сообщение от {sender}, '
                                          f'открыть чат с ним?', QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print('NO')
                # Если нет, спрашиваем хотим ли добавить пользователя в контакты
                if self.messages.question(self, 'Новое сообщение', f'Получено новое сообщение от {sender}.\n '
                                          f'Данного пользователя нет в вашем контакт-листе.\n '
                                          f'Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    # Слот потери соединения. Выдаёт сообщение об ошибке и завершает работу приложения
    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером!')
        self.close()

    def make_connection(self, trans_obj):
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)
