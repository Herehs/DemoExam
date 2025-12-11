from functools import partial

from PyQt6.QtCore import QDate, Qt
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

        dlg = product_edit_window(self)

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
        dlg.setData(self.db)
        dlg.connect_signals()

        res = dlg.exec()
        if res == QDialog.DialogCode.Accepted:
            self.refresh_cards()

    def goto_orders(self):
        dlg = OrderListWindow(self.db)
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
    def set_data(self, username=None, user_role= None):
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
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.cards = []
        self.selected_card = None
        self.setupUi(self)
        self.refreshOrders()


    def card_clicked(self, card):
        if self.selected_card and self.selected_card != card:
            self.selected_card.set_selected(False)

        self.selected_card = card
        card.set_selected(True)

    # ----- ОБРАБОТКА ДВОЙНОГО КЛИКА (ВЫЗОВ ОКНА РЕДАКТИРОВАНИЯ) -----
    def card_double_clicked(self, card):

        dlg2 = EditOrderWindow(77, self.db)
        dlg2.set_data(id=card.id, status=card.status,
                      address=card.address, order_date=card.order_date, delivery_date=card.delivery_date)
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
                SELECT o.product_id, o.order_id, o.order_status, p.address, o.order_date, o.delivery_date
                FROM orders as o
                JOIN pick_up_point as p
                ON o.pick_up_point_id = p.pick_up_point_id;
           """

        try:
            result = self.db.execute_query(query, fetch=True)
            if result:
                for row in result:
                    print(row)
                    product_id, order_id, status, address, order_date, delivery_date = row
                    order_card = OrderDataWidget(
                        id= order_id,
                        status= status,
                        address= address,
                        order_date= order_date.strftime("%Y-%m-%d"),
                        delivery_date= delivery_date.strftime("%Y-%m-%d"),
                    )
                    self.cards.append(order_card)

            else:
                print("Ошибка загрузки заказов.")


        except Exception as e:
            print(f"Ошибка загрузки заказов: {e}")

        for card in self.cards:
            card.clicked.connect(partial(self.card_clicked, card))
            card.doubleClicked.connect(partial(self.card_double_clicked, card))
            print(f"Создана карточка заказа: {order_card}")
            self.verticalLayout_12.addWidget(card)

    def connect_signals(self):
        self.order_button_back.clicked.connect(self.close)



class AddOrderWindow(QDialog, Ui_order_edit):
    def __init__(self, user_id, db):
        super().__init__()
        self.setupUi(self)
        self.user_id = user_id
        self.quantity = 1
        self.db = db
        self.fetch_products()
        self.fetch_pick_up_points()


    def connect_signals(self):
        self.save_button.clicked.connect(self.save_to_db)
        self.save_button.clicked.connect(self.accept)

    def save_to_db(self):
        query = """
                    UPDATE orders SET
                        
                    WHERE product_id = %s;
                """
        params = (

            self.status_input.text(),
            self.adres_input.currentText(),
            self.date_order.toPlainText(),
            self.delivery_date.text(),

            self.articul_input.currentText(),
        )
        try:
            result = self.db.execute_query(query, params, fetch=False)
            if not result:
                print("Ошибка добавления.")

        except Exception as e:
            print(f"Ошибка добавления: {e}")

    def fetch_pick_up_points(self):
        query = """
                   SELECT DISTINCT address FROM pick_up_point;
               """
        try:
            result = self.db.execute_query(query, fetch=True)
            self.adres_input.clear()

            if result:
                for (address,) in result:
                    print(address)
                    self.adres_input.addItem(address)

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
            self.adres_input.clear()

            if result:
                for row in result:
                    product_id, name  = row
                    print(f"АРТ: {product_id}. {name}")
                    self.product_input.addItem(f"АРТ: {product_id}. {name}")

            else:
                print("Ошибка загрузки заказов.")

        except Exception as e:
            print(f"Ошибка загрузки заказов: {e}")

    def save_to_db(self):
        print("save_to_db")

class EditOrderWindow(AddOrderWindow):
    def __init__(self, user_id, db):
        super().__init__(user_id, db= db)
        self.db = db

    def set_data(self, id, status, address, order_date, delivery_date):

        self.id = id
        self.status = status
        self.address = address
        self.order_date = order_date
        self.delivery_date_str = delivery_date



        self.articul_input.setText(f"{self.id}")
        self.status_input.setCurrentText(self.status)
        self.cancel_button.clicked.connect(self.close)
        self.date_order.setDate(QDate.fromString(self.order_date, "yyyy-MM-dd"))
        self.delivery_date.setDate(QDate.fromString(self.delivery_date_str, "yyyy-MM-dd"))

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
