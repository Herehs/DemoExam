import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QPushButton, QVBoxLayout, QLabel,
    QStackedWidget
)
from presentation.login_window import Ui_Login
from presentation.products import Ui_List_of_products



class LoginWindow(QMainWindow, Ui_Login):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        self.connect_signals()
        self.manager.resize(452, 507)

    def connect_signals(self):
        self.login_button.clicked.connect(self.handle_login)

    def handle_login(self):
        print("--- 🔴 Функция handle_login вызвана! ---")
        self.manager.goto_window("MainWindow")
        self.manager.resize(1028, 599)


class ProductListWindow(QMainWindow, Ui_List_of_products):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setupUi(self)



class WindowManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Главный Контроллер Окон")


        self.stack = QStackedWidget()

        self.windows = {}

        self.setCentralWidget(self.stack)

        """
        Экран авторизации
        """
        login_window_instance = LoginWindow(self)
        self.stack.addWidget(login_window_instance)
        self.windows["LoginWindow"] = login_window_instance

        """
        Экран продуктов
        """
        product_window_instance = ProductListWindow(self)
        self.stack.addWidget(product_window_instance)
        self.windows["MainWindow"] = product_window_instance

        self.goto_window("LoginWindow")

    def goto_window(self, name):
        """
        Метод-контроллер для переключения окон в QStackedWidget.
        """
        # Здесь нет ошибки, так как self.windows уже создан в __init__
        if name in self.windows:
            widget = self.windows[name]
            self.stack.setCurrentWidget(widget)
        else:
            print(f"Ошибка: Окно с именем '{name}' не найдено.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager = WindowManager()
    manager.show()
    sys.exit(app.exec())