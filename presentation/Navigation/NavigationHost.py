import random
import re
from functools import partial

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QDialog, QListView

from presentation.Edit_order_UI.order_edit_window import Ui_order_edit
from presentation.Login_UI.login_window import Ui_Login
from presentation.Order_list_UI.order_data import OrderDataWidget
from presentation.Order_list_UI.order_list_window import Ui_Dialog
from presentation.Product_list_UI.products import Ui_List_of_products
from presentation.Product_list_UI.widget import ProductCardUI
from presentation.Product_edit_UI.product_edit_window import product_edit_window, product_add_window


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

        self.cards = []

        self.setupUi(self, db)
        self.connect_signals()
        self.load_providers()

        # -----------------------------
        # Скрытие кнопок
        # -----------------------------

        self.sort_input.hide()
        self.provider_input.hide()
        self.search_input.hide()
        self.add_product_button.hide()
        self.delete_product_button.hide()
        self.order_button.hide()

        self.cards = self.query_from_DB()
        self.selected_card = None
        for card in self.cards:
            card.clicked.connect(partial(self.card_clicked, card))
            card.doubleClicked.connect(partial(self.card_double_clicked, card))
            self.scrollLayout.addWidget(card)

    def refresh_cards(self):
        # удалить старые карточки
        while self.scrollLayout.count():
            item = self.scrollLayout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        # загрузить новые
        self.cards = self.query_from_DB()
        for card in self.cards:
            card.disconnect_all()
            card.clicked.connect(partial(self.card_clicked, card))
            card.doubleClicked.connect(partial(self.card_double_clicked, card))
            self.scrollLayout.addWidget(card)

    # ----- ОБРАБОТКА ОДИНОЧНОГО КЛИКА (ВЫДЕЛЕНИЕ) -----
    def card_clicked(self, card):
        if self.selected_card and self.selected_card != card:
            self.selected_card.set_selected(False)

        self.selected_card = card
        card.set_selected(True)

    # ----- ОБРАБОТКА ДВОЙНОГО КЛИКА (ВЫЗОВ ОКНА РЕДАКТИРОВАНИЯ) -----
    def card_double_clicked(self, card):
        if self.user_role == "Администратор":
            dlg = product_edit_window(self)
            dlg.setWindowIcon(QIcon("res/icons/Icon.JPG"))
            dlg.setWindowTitle("Редактирование товара")
            dlg.setData(
                db=self.db,
                id=card.id,
                name= f"{card.name}",
                category= f"{card.category}",
                description=f"{card.description}",
                manufacturer=f"{card.manufacturer}",
                supplier=f"{card.supplier}",
                price=f"{card.price}",
                unit=f"{card.unit}",
                quantity=f"{card.quantity}",
                discount_percent=f"{card.discount_percent}",
                image_path= card.image_path,
            )
            dlg.connect_signals()

            res = dlg.exec()
            if res == QDialog.DialogCode.Accepted:
                self.refresh_cards()

    # ----- ПОДКЛЮЧЕНИЕ КНОПОК К ИНТЕРФЕЙСУ -----
    def connect_signals(self):
        self.logout_button.clicked.connect(self.handle_logout)
        self.add_product_button.clicked.connect(self.add_product)
        self.delete_product_button.clicked.connect(self.delete_product)
        self.order_button.clicked.connect(self.goto_orders)

        self.search_input.textChanged.connect(self.apply_filters)
        self.sort_input.currentIndexChanged.connect(self.apply_filters)
        self.provider_input.currentIndexChanged.connect(self.apply_filters)

    # ----- ОБРАБОТКА УДАЛЕНИЯ ТОВАРА -----
    def delete_product(self):
        try:
            self.cards.remove(self.selected_card)
            self.db.execute_query("DELETE FROM Products WHERE product_id = %s", [self.selected_card.id], fetch=False)
            self.refresh_cards()
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            return

    # ----- ОБРАБОТКА ДОБАВЛЕНИЯ ТОВАРА -----
    def add_product(self):
        dlg = product_add_window(self)
        dlg.setWindowIcon(QIcon("res/icons/Icon.JPG"))
        dlg.setWindowTitle("Добавление товара")
        dlg.setData(self.db)
        dlg.connect_signals()

        res = dlg.exec()
        if res == QDialog.DialogCode.Accepted:
            self.refresh_cards()

    def goto_orders(self):
        dlg = OrderListWindow(self.db, self.role)
        dlg.setWindowIcon(QIcon("res/icons/Icon.JPG"))
        dlg.setWindowTitle("Заказы")
        dlg.setMinimumWidth(600)
        dlg.connect_signals()

        dlg.exec()

    # ----- ОБРАБОТКА ВЫХОДА -----
    def handle_logout(self):
        self.manager.goto_window("LoginWindow")
        self.sort_input.hide()
        self.provider_input.hide()
        self.search_input.hide()
        self.add_product_button.hide()
        self.delete_product_button.hide()
        self.order_button.hide()

    # ----- ЗАПРОС ДАННЫХ ДЛЯ ВСЕХ ТОВАРОВ -----
    def query_from_DB(self):


        query = """
        SELECT product_id, category, name, description, manufacturer, supplier, price, unit_of_measurement, discount, photo, quantity
    FROM products;
    """

        try:
            result = self.db.execute_query(query, fetch=True)
            cards = []
            if result:
                for row in result:
                    product_id, category, name, description, manufacturer, supplier, price, unit, discount, photo, quantity = row

                    if photo == '':
                        photo = "picture.png"

                    product_card = ProductCardUI(
                        id=product_id,
                        category=category,
                        name=f"{name}",
                        description=f"{description}",
                        manufacturer=f"{manufacturer}",
                        supplier=f"{supplier}",
                        price=f"{price}",
                        unit=f"{unit}",
                        discount_percent=f"{discount}",
                        quantity=f"{quantity}",
                        image_path= photo
                    )
                    s = f"""
                        QWidget {{
                            border-color: 00FA9A;
                        }}
                        """
                    product_card.setStyleSheet(s)
                    cards.append(product_card)

                return cards
            else:
                print("Ошибка аутентификации: неверный логин или пароль.")
                return False

        except Exception as e:
            print(f"Ошибка при аутентификации: {e}")
            return False

    # ----- ПЕРЕДАЧА ДАННЫХ ИЗ ОКНА АВТОРИЗАЦИИ В ОКНО ТОВАРОВ -----
    def set_data(self, username=None, user_role= None, user_id=None):
        if username:
            self.username = username
            print("Получено имя пользователя:", username)
            self.user_fio.setText(username)
        if user_role:
            self.user_role = user_role
            print(user_role)

            self.role = user_role.strip()

            if self.role == "Гость":
                print("gost zaza")
            elif self.role == "Менеджер":
                self.sort_input.show()
                self.provider_input.show()
                self.search_input.show()
                self.order_button.show()
                print("menedjer zaza")
            elif self.role == "Администратор":
                self.sort_input.show()
                self.provider_input.show()
                self.search_input.show()
                self.add_product_button.show()
                self.delete_product_button.show()
                self.order_button.show()
                print("administrator zaza")

    # ----- ЗАГРУЗКА ПОСТАВЩИКОВ ДЛЯ ФИЛЬТРА ПО ПОСТАВЩИКАМ -----
    def load_providers(self):
        query = "SELECT DISTINCT supplier FROM products"
        result = self.db.execute_query(query, fetch=True)

        self.provider_input.clear()
        self.provider_input.addItem("Все поставщики")

        if result:
            for (supplier,) in result:
                self.provider_input.addItem(supplier)

    # ----- ПРИМЕНЕНИЕ ФИЛЬТРОВ И ПОИСКА -----
    def apply_filters(self):
        search_text = self.search_input.text().lower().strip()
        sort_mode = self.sort_input.currentText()
        provider = self.provider_input.currentText()

        filtered = list(self.cards)

        # фильтр по поиску
        if search_text:
            words = search_text.split()

            def matches(card):
                text = " ".join([
                    card.name.lower(),
                    card.description.lower(),
                    card.manufacturer.lower(),
                    card.supplier.lower(),
                    card.price.lower(),
                ])
                return all(w in text for w in words)

            filtered = [c for c in filtered if matches(c)]

        # фильтр по поставщику
        if provider != "Все поставщики":
            filtered = [c for c in filtered if c.supplier == provider]

        # фильтр по возрастанию/убыванию цены
        try:
            if sort_mode == "Количество по возрастанию":
                filtered = sorted(filtered, key=lambda c: float(c.quantity))
            elif sort_mode == "Количество по убыванию":
                filtered = sorted(filtered, key=lambda c: float(c.quantity), reverse=True)
        except:
            pass

        # обновление виджетов
        while self.scrollLayout.count():
            item = self.scrollLayout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        for card in filtered:
            self.scrollLayout.addWidget(card)

class OrderListWindow(QDialog, Ui_Dialog):
    def __init__(self, db, user_role):
        super().__init__()
        self.db = db
        self.user_role = user_role
        self.cards = []
        self.selected_card = None
        self.setupUi(self)
        self.refreshOrders()

        if user_role != "Администратор":
            self.order_button_remove.hide()
            self.order_button_add.hide()
        else:
            self.order_button_remove.show()
            self.order_button_add.show()

    def card_clicked(self, card):
        if self.selected_card and self.selected_card != card:
            self.selected_card.set_selected(False)

        self.selected_card = card
        card.set_selected(True)

    # ----- ОБРАБОТКА ДВОЙНОГО КЛИКА (ВЫЗОВ ОКНА РЕДАКТИРОВАНИЯ) -----
    def card_double_clicked(self, card):

        dlg2 = EditOrderWindow(self.db)
        dlg2.setWindowIcon(QIcon("res/icons/Icon.JPG"))
        dlg2.setWindowTitle("Редактирование заказа")
        dlg2.set_data(id=card.id, status=card.status,
                      address=card.address, order_date=card.order_date,
                      delivery_date=card.delivery_date, quantity= card.quantity,
                      username= card.username, product_id= card.product_id, user_id=card.user_id)
        dlg2.connect_signals()

        res = dlg2.exec()
        if res == QDialog.DialogCode.Accepted:
            self.refreshOrders()

    def refreshOrders(self):
        # удалить старые карточки
        while self.verticalLayout_12.count():
            item = self.verticalLayout_12.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        #-------------------------
        self.cards = []

        query = """
                SELECT o.product_id, o.order_id, o.order_status, p.address, o.order_date, o.delivery_date, o.quantity, u.full_name, u.user_id, p.pick_up_point_id
                FROM orders as o
                JOIN pick_up_point as p
                ON o.pick_up_point_id = p.pick_up_point_id
                JOIN users as u
                ON o.user_id = u.user_id;
           """

        try:
            result = self.db.execute_query(query, fetch=True)
            if result:
                for row in result:
                    print(row)
                    product_id, order_id, status, address, order_date, delivery_date, quantity, username, user_id, pick_up_point_id = row
                    order_card = OrderDataWidget(
                        id= order_id,
                        status= status,
                        address= f"{pick_up_point_id}: {address}",
                        order_date= order_date.strftime("%Y-%m-%d"),
                        delivery_date= delivery_date.strftime("%Y-%m-%d"),
                        quantity= quantity,
                        username= username,
                        product_id= product_id,
                        user_id= user_id
                    )
                    self.cards.append(order_card)

            else:
                print("Ошибка загрузки заказов.")


        except Exception as e:
            print(f"Ошибка загрузки заказов: {e}")

        for card in self.cards:
            card.clicked.connect(partial(self.card_clicked, card))
            if self.user_role == "Администратор":
                card.doubleClicked.connect(partial(self.card_double_clicked, card))
            self.verticalLayout_12.addWidget(card)

    def connect_signals(self):
        self.order_button_back.clicked.connect(self.close)
        self.order_button_add.clicked.connect(self.add_order)
        self.order_button_remove.clicked.connect(self.remove_order)

    def remove_order(self):
        self.cards.remove(self.selected_card)
        self.db.execute_query("DELETE FROM orders WHERE order_id = %s", [self.selected_card.id], fetch=False)
        self.refreshOrders()

    def add_order(self):
        dlg2 = AddOrderWindow(self.db)
        dlg2.setWindowIcon(QIcon("res/icons/Icon.JPG"))
        dlg2.setWindowTitle("Добавление заказа")
        dlg2.connect_signals()

        res = dlg2.exec()
        if res == QDialog.DialogCode.Accepted:
            self.refreshOrders()

class AddOrderWindow(QDialog, Ui_order_edit):
    def __init__(self, db):
        super().__init__()
        self.setupUi(self)
        self.quantity = 1
        self.db = db
        self.fetch_products()
        self.fetch_pick_up_points()
        self.fetch_users()


        self.id = self.fetch_max_order_id() + 1
        self.articul_input.setText(str(self.id))
        self.status = None
        self.address = None
        self.quantity = None
        self.username = None
        self.order_date = None
        self.delivery_date_str = None
        self.product_id = None



    def connect_signals(self):
        self.save_button.clicked.connect(self.save_to_db)
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.close)

    def save_to_db(self):

        user_id = self.client_name_input.currentText().split(":")[0]  # Извлекаем user_id из поля с полным именем
        pick_up_point_id = self.adres_input.currentText().split(":")[0]  # Извлекаем pick_up_point_id из поля с адресом
        str = self.product_input.currentText().split(":")[1].strip()
        product_id = str.split(".")[0].strip()
        order_status = self.status_input.currentText()  # Статус заказа
        order_date = self.date_order.date().toString("yyyy-MM-dd")  # Дата заказа
        delivery_date = self.delivery_date.date().toString("yyyy-MM-dd")  # Дата доставки
        quantity = self.count_input.text()  # Количество товара
        order_code = random.randint(100, 999)

        query = """
            INSERT INTO orders (
            user_id, 
            pick_up_point_id, 
            product_id, 
            order_status, 
            order_code,
            order_date, 
            delivery_date, 
            quantity
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """

        params = (
            user_id,
            pick_up_point_id,
            product_id,
            order_status,
            order_code,
            order_date,
            delivery_date,
            quantity,
        )

        try:
            self.db.execute_query(query, params, fetch=False)
            print("Заказ успешно добавлен!")

        except Exception as e:
            print(f"Ошибка при добавлении заказа: {e}")

    def fetch_pick_up_points(self):
        query = """
                   SELECT DISTINCT pick_up_point_id, address FROM pick_up_point;
               """
        try:
            result = self.db.execute_query(query, fetch=True)
            self.adres_input.clear()
            self.adres_input.addItem("Не выбран")
            if result:
                for row in result:
                    pick_up_point_id, address = row
                    self.adres_input.addItem(f"{pick_up_point_id}: {address}")

            else:
                print("Ошибка загрузки заказов.")

        except Exception as e:
            print(f"Ошибка загрузки заказов: {e}")

    def fetch_products(self):
        query = """
                  SELECT product_id, name FROM products;
              """
        try:
            result = self.db.execute_query(query, fetch=True)
            self.product_input.clear()
            self.product_input.addItem("Не выбран")

            if result:
                for row in result:
                    product_id, name  = row
                    # print(f"АРТ: {product_id}. {name}")
                    self.product_input.addItem(f"АРТ: {product_id}. {name}")

            else:
                print("Ошибка загрузки заказов.")

        except Exception as e:
            print(f"Ошибка загрузки заказов: {e}")

    def fetch_users(self):

        query = """
                  SELECT user_id, full_name FROM users;
              """
        try:
            result = self.db.execute_query(query, fetch=True)
            self.client_name_input.clear()
            self.client_name_input.addItem("Не выбрано")

            if result:
                for row in result:
                    id, full_name = row
                    self.client_name_input.addItem(f"{id}: {full_name}")

            else:
                print("Ошибка загрузки заказов.")

        except Exception as e:
            print(f"Ошибка загрузки заказов: {e}")

    def get_product_name(self, product_id):
        """
        Получаем имя продукта по его ID
        """
        query = "SELECT name FROM products WHERE product_id = %s"
        try:
            result = self.db.execute_query(query, [product_id], fetch=True)
            if result:
                return result[0][0]  # Возвращаем имя продукта
            else:
                return "Не найдено"  # Если продукт не найден
        except Exception as e:
            print(f"Ошибка при получении имени продукта: {e}")
            return "Ошибка"

    def fetch_max_order_id(self):
        query = """ SELECT MAX(order_id) FROM orders; """
        try:
            result = self.db.execute_query(query, fetch=True)
            if result:
                for (id,) in result:
                    return id
            else:
                print("Ошибка загрузки заказов.")

        except Exception as e:
            print(f"Ошибка загрузки заказов: {e}")

class EditOrderWindow(AddOrderWindow):
    def __init__(self, db):
        super().__init__(db= db)
        self.db = db

    def set_data(self, id, status, address, username, user_id,quantity, order_date, delivery_date, product_id):

        self.id = id
        self.status = status
        self.address = address
        self.quantity = quantity
        self.username = username
        self.order_date = order_date
        self.delivery_date_str = delivery_date
        self.product_id = product_id
        self.user_id = user_id

        print(address)
        self.articul_input.setText(f"{self.id}")
        self.status_input.setCurrentText(self.status)
        self.adres_input.setCurrentText(self.address)
        self.client_name_input.setCurrentText(f"{self.user_id}: {self.username}")
        product_text = f"АРТ: {self.product_id}. {self.get_product_name(self.product_id)}"
        self.product_input.setCurrentText(product_text)

        self.count_input.setText(f"{self.quantity}")

        self.date_order.setDate(QDate.fromString(self.order_date, "yyyy-MM-dd"))
        self.delivery_date.setDate(QDate.fromString(self.delivery_date_str, "yyyy-MM-dd"))

    def save_to_db(self):

        user_id = self.client_name_input.currentText().split(":")[0]  # Извлекаем user_id из поля с полным именем
        pick_up_point_id = self.adres_input.currentText().split(":")[0]  # Извлекаем pick_up_point_id из поля с адресом
        str = self.product_input.currentText().split(":")[1].strip()
        product_id = str.split(".")[0].strip()
        order_status = self.status_input.currentText()  # Статус заказа
        order_date = self.date_order.date().toString("yyyy-MM-dd")  # Дата заказа
        delivery_date = self.delivery_date.date().toString("yyyy-MM-dd")  # Дата доставки
        quantity = self.count_input.text()  # Количество товара
        order_code = random.randint(100, 999)

        query = """
            UPDATE orders SET
                user_id = %s,
                pick_up_point_id = %s,
                product_id = %s,
                order_status = %s,
                order_code = %s,
                order_date = %s,
                delivery_date = %s,
                quantity = %s
            WHERE order_id = %s;
        """

        params = (
            user_id,
            pick_up_point_id,
            product_id,
            order_status,
            order_code,
            order_date,
            delivery_date,
            quantity,
            self.id
        )

        try:
            self.db.execute_query(query, params, fetch=False)
            print("Заказ успешно добавлен!")

        except Exception as e:
            print(f"Ошибка при добавлении заказа: {e}")


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
