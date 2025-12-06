from database.database import DBController


class User:
    def __init__(self, user_id, user_role, full_name):
        self.user_id = user_id
        self.user_role = user_role
        self.full_name = full_name


class UserRepository:
    def __init__(self, db_controller: DBController):
        self._db = db_controller

    def search_user(self, user_login, password):
        query = """
                    SELECT user_id, user_role, full_name 
                    FROM Users 
                    WHERE user_login = %s AND user_password = %s
                """
        params = (user_login, password)

        try:
            result = self._db.execute_query(query, params, fetch=True)

            if result:
                user_id, user_role, full_name,  = result[0]
                print(f"Аутентификация успешна для пользователя: ID={user_id}, Роль='{user_role}'")
                return User(user_id, user_role, full_name)
            else:
                print("Ошибка аутентификации: неверный логин или пароль.")
                return None
        except Exception as e:
            print(f"Ошибка при аутентификации: {e}")
            return None
