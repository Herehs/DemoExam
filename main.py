import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow
)

from database.database import DBController
from presentation.Navigation.NavigationHost import WindowManager








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
