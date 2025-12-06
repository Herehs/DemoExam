from PyQt6 import QtCore
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget

from presentation.Login_UI.login_window import Ui_Login
from presentation.Product_list_UI.products import Ui_List_of_products


class LoginWindow(QMainWindow, Ui_Login):
    def __init__(self, manager, VM):
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        self.connect_signals()
        self.VM = VM


    def connect_signals(self):
        self.login_button.clicked.connect(self.handle_login)
        self.guest_button.clicked.connect(self.handle_login_as_guest)

    def handle_login(self):
        username = self.login_input.text()
        password = self.password_input.text()
        if self.VM.login(username, password):
            self.manager.goto_window("MainWindow")
            self.manager.resize(1028, 599)


    def handle_login_as_guest(self):
        self.manager.goto_window("MainWindow")


class List_of_products_screen_UI(QMainWindow, Ui_List_of_products):
    def __init__(self, db, login_VM):
        super().__init__()
        self.db = db
        self.login_VM = login_VM
        self.query_from_DB()
        self.setupUi(self, db)



class WindowManager(QMainWindow):
    def __init__(self, loginVM, db):
        super().__init__()
        self.loginVM = loginVM
        self.db= db

        self.stack = QStackedWidget()

        self.windows = {}

        self.setCentralWidget(self.stack)

        """
        Экран авторизации
        """
        login_window_instance = LoginWindow(self, self.loginVM)
        self.stack.addWidget(login_window_instance)
        self.windows["LoginWindow"] = login_window_instance

        """
        Экран продуктов
        """
        product_window_instance = List_of_products_screen_UI(self.db, login_VM= loginVM)
        self.stack.addWidget(product_window_instance)
        self.windows["MainWindow"] = product_window_instance
        self.goto_window("LoginWindow")

    def goto_window(self, name):
        """
        Метод-контроллер для переключения окон в QStackedWidget.
        """
        # Здесь нет ошибки, так как self.windows уже создан в __init__
        if name == "LoginWindow":
            self.setFixedSize(452, 507)
            self.setWindowTitle("Авторизация")
        elif name == "MainWindow":
            self.setFixedSize(1028, 599)
            self.setWindowTitle("Список товаров")


        if name in self.windows:
            widget = self.windows[name]
            self.stack.setCurrentWidget(widget)
        else:
            print(f"Ошибка: Окно с именем '{name}' не найдено.")
