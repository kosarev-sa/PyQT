import sys
from logging import getLogger
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

sys.path.append('../')

log = getLogger('client')


class DelContactDialog(QDialog):        # Диалог выбора контакта для удаления
    def __init__(self, database):
        super().__init__()
        self.db = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Выбор контакта для удаления')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для удаления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton('Удалить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Отменить', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.selector.addItems(sorted(self.db.get_contacts()))        # заполнитель контактов для удаления
