import sys
from logging import getLogger
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

sys.path.append('../')

log = getLogger('client')


class AddContactDialog(QDialog):
    '''Диалог выбора контакта для добавления.'''
    def __init__(self, transport, database):
        super().__init__()
        self.s = transport
        self.db = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Выбор контакта для добавления')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для добавления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_refresh = QPushButton('Обновление списка', self)
        self.btn_refresh.setFixedSize(100, 30)
        self.btn_refresh.move(60, 60)

        self.btn_ok = QPushButton('Добавить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Отменить', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.possible_contacts_update()  # Заполняем список возможных контактов

        # Назначаем действие на кнопку обновить
        self.btn_refresh.clicked.connect(self.update_possible_contacts)

    # Заполняем список возможных контактов разницей между всеми пользователями
    # и контактами клиента
    def possible_contacts_update(self):
        self.selector.clear()
        contacts_lst = set(self.db.get_contacts())
        users_lst = set(self.db.get_known_users())
        # Удалим себя из списка пользователей, чтобы нельзя было добавить
        # самого себя
        users_lst.remove(self.s.username)
        # Добавляем список возможных контактов
        self.selector.addItems(users_lst - contacts_lst)

    # Обновление возможных контактов. Обновляет таблицу известных
    # пользователей и содержимое предполагаемых контактов
    def update_possible_contacts(self):
        try:
            self.s.user_list_update()
        except OSError:
            pass
        else:
            log.debug('Обновление списка пользователей с сервера выполнено')
            self.possible_contacts_update()
