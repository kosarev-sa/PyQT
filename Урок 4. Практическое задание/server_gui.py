import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
import os


# GUI - Создание таблицы QModel, для отображения в окне программы
def gui_create_model(database):
    users_lst = database.active_users_lst()  # Список активных пользователей
    lst_ = QStandardItemModel()              # Начинка в главную форму (в разметку) QTableView
    lst_.setHorizontalHeaderLabels(['Клиент', 'IP', 'Порт', 'Время подключения'])
    for row in users_lst:
        user, ip, port, time = row
        user = QStandardItem(user)            # Создаем элемент
        user.setEditable(False)               # Редактирование
        ip = QStandardItem(ip)
        ip.setEditable(False)
        port = QStandardItem(str(port))
        port.setEditable(False)
        # Уберём милисекунды из строки времени, т.к. такая точность не требуется
        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)
        lst_.appendRow([user, ip, port, time])  # Добавляем строку
    return lst_


# GUI - Функция реализует заполнение таблицы историей сообщений
def create_stat_model(database):
    # Список записей из базы
    history_lst = database.msg_history()

    # Объект модели данных:
    lst = QStandardItemModel()
    lst.setHorizontalHeaderLabels(
        ['Клиент', 'Последнее подключение', 'Сообщений отправлено', 'Сообщений получено'])
    for row in history_lst:
        user, last_login, sent, recvd = row

        user = QStandardItem(user)
        user.setEditable(False)

        last_login = QStandardItem(str(last_login.replace(microsecond=0)))
        last_login.setEditable(False)

        sent = QStandardItem(str(sent))
        sent.setEditable(False)

        recvd = QStandardItem(str(recvd))
        recvd.setEditable(False)

        lst.appendRow([user, last_login, sent, recvd])
    return lst


# Класс основного окна
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Кнопка выхода
        exitAction = QAction('Выйти', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(qApp.quit)

        # Кнопка обновить список клиентов
        self.refresh_button = QAction('Обновить список', self)

        # Кнопка настроек сервера
        self.config_btn = QAction('Настройки сервера', self)

        # Кнопка вывести историю количества сообщений
        self.show_history_button = QAction('Всего сообщений', self)

        # Статусбар
        # dock widget
        self.statusBar()

        # Тулбар
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_btn)

        # Настройки геометрии основного окна (размер окна фиксирован).
        self.setFixedSize(800, 600)
        self.setWindowTitle('Messaging Server GUI')

        # Надпись о том, что ниже список подключённых клиентов
        self.label = QLabel('Список клиентов онлайн:', self)
        self.label.setFixedSize(240, 15)
        self.label.move(10, 30)

        # Окно со списком подключённых клиентов (по умолчанию без шапки)
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 45)
        self.active_clients_table.setFixedSize(780, 400)

        # Последним параметром отображаем окно
        self.show()


# Класс окна с историей пользователей
class HistoryWindow(QDialog):
    # QWidget в QDialog. Нет развертывания и скрытия только 2 кнопки 'скрыть' и '?'
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна:
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # Лист с историей
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


# Класс окна настроек
class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна
        self.setFixedSize(380, 260)
        self.setWindowTitle('Настройки сервера')

        # Надпись о файле базы данных:
        self.db_path_label = QLabel('База данных (путь до файла): ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        # Строка с путём базы
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # Кнопка выбора пути.
        self.db_path_select = QPushButton('Проводник', self)
        self.db_path_select.move(275, 28)

        # Функция обработчик открытия окна выбора папки
        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        # Метка с именем поля файла базы данных
        self.db_file_label = QLabel('Название файла БД: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        # Поле для ввода имени файла
        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        # Метка с номером порта
        self.port_label = QLabel('Порт для подключений:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        # Поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(150, 20)

        # Метка с адресом для соединений
        self.ip_label = QLabel('IP адрес для подключений к серверу:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        # Метка с напоминанием о пустом поле.
        self.ip_label_note = QLabel(' оставьте это поле пустым, чтобы\n принимать соединения с любых адресов.', self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        # Поле для ввода ip
        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        # Кнопка сохранения настроек
        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.move(190, 220)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':
    # app = QApplication(sys.argv)
    # ex = MainWindow()
    # ex.statusBar().showMessage('SERVER RUNNING')
    # test_lst = QStandardItemModel(ex)
    # test_lst.setHorizontalHeaderLabels(['Клиент', 'IP', 'Порт', 'Время подключения'])
    # test_lst.appendRow([QStandardItem('1'), QStandardItem('2.2.2.2'), QStandardItem('3333')])
    # test_lst.appendRow([QStandardItem('4'), QStandardItem('5.2.2.2'), QStandardItem('6666')])
    # ex.active_clients_table.setModel(test_lst)
    # ex.active_clients_table.resizeColumnsToContents()
    # print('START')
    # app.exec_()
    # print('END')
    app = QApplication(sys.argv)
    message = QMessageBox
    dial = ConfigWindow()

    app.exec_()
