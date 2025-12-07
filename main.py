import sys

from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStyleFactory
)

from database.database import DBController
from presentation.Navigation.NavigationHost import WindowManager, LoginWindow


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


    app.setStyle('Fusion')
    app.setStyleSheet("QWidget {background-color: white; color: black;}")

    manager = WindowManager(db= controller)
    manager.show()
    sys.exit(app.exec())
