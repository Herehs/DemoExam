from PyQt6 import QtCore
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QLabel

from presentation.Login_UI.login_window import Ui_Login
from presentation.Product_list_UI.products import Ui_List_of_products


class LoginWindow(QMainWindow, Ui_Login):
    def __init__(self, manager, db):
        super().__init__()
        self.manager = manager
        self.db = db
        self.setupUi(self)
        self.connect_signals()

    def connect_signals(self):
        self.login_button.clicked.connect(self.handle_login)
        self.guest_button.clicked.connect(self.handle_login_as_guest)

    def handle_login(self):
        login = self.login_input.text()
        password = self.password_input.text()

        result, full_name, user_role = self.authenticate(login, password)

        if result:
            # Передаем имя пользователя в главное окно
            self.manager.goto_window("MainWindow", username=full_name, user_role=user_role)

    def authenticate(self, login, password):
        query = """
            SELECT user_id, user_role, full_name, user_role
            FROM Users 
            WHERE user_login = %s AND user_password = %s
        """
        params = (login, password)

        try:
            result = self.db.execute_query(query, params, fetch=True)

            if result:
                user_id, user_role, full_name, user_role = result[0]
                print(f"Аутентификация успешна: ID={user_id}, Роль={user_role}")
                return True, full_name, user_role
            else:
                print("Ошибка: неверный логин или пароль.")
                return False, None, None

        except Exception as e:
            print(f"Ошибка при аутентификации: {e}")
            return False, None, None

    def handle_login_as_guest(self):
        self.manager.goto_window("MainWindow", username="Гость", user_role="Гость")


class List_of_products_screen_UI(QMainWindow, Ui_List_of_products):
    def __init__(self, manager, db):
        super().__init__()
        self.db = db
        self.manager = manager
        self.username = None
        self.user_role = None
        self.setupUi(self, db)
        self.connect_signals()

        # -----------------------------
        # Скрытие кнопок
        # -----------------------------

        self.sort_input.hide()
        self.provider_input.hide()
        self.search_input.hide()
        self.add_product_button.hide()
        self.delete_product_button.hide()
        self.order_button.hide()


    def connect_signals(self):
        self.logout_button.clicked.connect(self.handle_logout)

    def handle_logout(self):
        self.manager.goto_window("LoginWindow")
        self.sort_input.hide()
        self.provider_input.hide()
        self.search_input.hide()
        self.add_product_button.hide()
        self.delete_product_button.hide()
        self.order_button.hide()



    def set_data(self, username=None, user_role= None):
        """
        Получает имя пользователя из LoginWindow через WindowManager
        """
        if username:
            self.username = username
            print("Получено имя пользователя:", username)
            self.user_fio.setText(username)
        if user_role:
            self.user_role = user_role
            print(user_role)

            role = user_role.strip()

            if role == "Гость":
                self.sort_input.show()
                self.provider_input.show()
                self.search_input.show()
                self.add_product_button.show()
                self.delete_product_button.show()
                self.order_button.show()
                print("gost zaza")
            elif role == "Менеджер":
                self.sort_input.show()
                self.provider_input.show()
                self.search_input.show()
                print("menedjer zaza")
            elif role == "Администратор":
                self.sort_input.show()
                self.provider_input.show()
                self.search_input.show()
                self.add_product_button.show()
                self.delete_product_button.show()
                self.order_button.show()
                print("administrator zaza")

class WindowManager(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db

        self.stack = QStackedWidget()
        self.windows = {}

        self.setCentralWidget(self.stack)

        # -----------------------------
        # Экран авторизации
        # -----------------------------
        login_window_instance = LoginWindow(self, db)
        self.stack.addWidget(login_window_instance)
        self.windows["LoginWindow"] = login_window_instance

        # -----------------------------
        # Экран товаров
        # -----------------------------
        product_window_instance = List_of_products_screen_UI(self, db)
        self.stack.addWidget(product_window_instance)
        self.windows["MainWindow"] = product_window_instance

        # Переходим в окно авторизации
        self.goto_window("LoginWindow")

    def goto_window(self, name, **kwargs):
        """
        Переключение окон + передача параметров (например username)
        """

        if name == "LoginWindow":
            self.setFixedSize(452, 507)
            self.setWindowTitle("Авторизация")

        elif name == "MainWindow":
            self.setFixedSize(1123, 645)
            self.setWindowTitle("Список товаров")

        # Переключение окна
        if name in self.windows:
            widget = self.windows[name]

            # Передаём параметры (например username)
            if hasattr(widget, "set_data"):
                widget.set_data(**kwargs)

            self.stack.setCurrentWidget(widget)
        else:
            print(f"Ошибка: окно '{name}' не найдено.")
