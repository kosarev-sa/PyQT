from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel , qApp
from PyQt5.QtCore import QEvent


class UserNameDialog(QDialog):      # Стартовый диалог с выбором имени пользователя
    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle('Здравствуйте!')
        self.setFixedSize(250, 100)

        self.label = QLabel('Введите Ваше имя:', self)
        self.label.move(10, 10)
        self.label.setFixedSize(150, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.btn_ok = QPushButton('Начать', self)
        self.btn_ok.move(10, 60)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Выйти', self)
        self.btn_cancel.move(120, 60)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    def click(self):               # Обработчик кнопки ОК, если поле вводе не пустое, ставим флаг и завершаем приложение
        if self.client_name.text():
            self.ok_pressed = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserNameDialog()
    app.exec_()
