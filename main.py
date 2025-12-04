import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QPushButton, QVBoxLayout, QLabel,
    QStackedWidget
)
from presentation.login_window import Ui_Login
from presentation.products import Ui_List_of_products
from database.database import DBController


class LoginWindow(QMainWindow, Ui_Login):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        self.connect_signals()
        self.manager.resize(452, 507)

    def connect_signals(self):
        self.login_button.clicked.connect(self.handle_login)
        self.guest_button.clicked.connect(self.handle_login_as_guest)

    def handle_login(self):

        def _authenticate(user, psw):
            query = """
                            SELECT user_id, user_role 
                            FROM Users 
                            WHERE user_login = %s AND user_password = %s
                        """
            params = (user, psw)

            try:
                result = controller.execute_query(query, params, fetch=True)

                if result:
                    user_id, user_role = result[0]
                    print(f"Аутентификация успешна для пользователя: ID={user_id}, Роль='{user_role}'")
                    return True
                else:
                    print("Ошибка аутентификации: неверный логин или пароль.")
                    return False

            except Exception as e:
                print(f"Ошибка при аутентификации: {e}")
                return False

        def _process_credentials(username, password):
            clean_username = username.strip()
            if not clean_username:
                print("Ошибка: Поле логина не может быть пустым.")
                return
            if not password:
                print("Ошибка: Поле пароля не может быть пустым.")
                return
            print(f"Пользователь: {clean_username} пытается войти.")
            if _authenticate(clean_username, password):
                self.manager.goto_window("MainWindow")
                self.manager.resize(1028, 599)
            else:
                print("Ошибка: Неверный логин или пароль.")

        print("--- 🔴 Функция handle_login вызвана! ---")

        username = self.login_input.text()
        password = self.password_input.text()
        _process_credentials(username, password)

    def handle_login_as_guest(self):
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
    """
    Подключение БД
    """
    DB_NAME = "shoesdb"
    DB_USER = "me"
    DB_PASS = "1488"
    DB_HOST = "localhost"
    DB_PORT = "5432"

    controller = DBController(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT)

    """
    Отрисовка UI
    """
    app = QApplication(sys.argv)
    manager = WindowManager()
    manager.show()
    sys.exit(app.exec())