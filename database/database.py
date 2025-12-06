import psycopg



class DBController:
    def __init__(self, dbname, user, password, host, port):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                autocommit=False
            )
            print("Соединение с базой данных установлено.")
        except psycopg.Error as e:
            print(f"Ошибка при подключении к базе данных: {e}")
            raise

    def disconnect(self):
        if self.conn:
            self.conn.close()
            print("Соединение с базой данных закрыто.")

    def execute_query(self, query, params=None, fetch=False):
        if not self.conn or self.conn.closed:
            self.connect()

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)

                if fetch:
                    return cur.fetchall()
                else:
                    self.conn.commit()
                    return None

        except psycopg.Error as e:
            self.conn.rollback()
            print(f"Ошибка выполнения запроса: {e}")
            raise
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
            raise




if __name__ == '__main__':
    DB_NAME = "shoesdb"
    DB_USER = "me"
    DB_PASS = "1488"
    DB_HOST = "localhost"
    DB_PORT = "5432"

    controller = DBController(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT)

    try:
        controller.connect()

        select_query = """
                        SELECT user_id, user_role 
                        FROM Users 
                        WHERE user_login = 'l' AND user_password = 'l'
        """
        results = controller.execute_query(select_query, fetch=True)
        if results:
            print("\nПример выборки данных из Orders:")
            for row in results:
                print(row)
        else:
            print("ne robit")
    except Exception as e:
        print(f"\nРабота программы завершена с ошибкой: {e}")
    finally:
        controller.disconnect()