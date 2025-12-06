class LoginViewModel:
    def __init__(self, user_repository):
        self._repository = user_repository
        self._current_user = None
        self._error_message = ""
        self._is_authenticated = False

    @property
    def current_user(self):
        return self._current_user

    @property
    def error_message(self):
        return self._error_message

    @property
    def is_authenticated(self):
        return self._is_authenticated

    def login(self, username, password):
        user = self._repository.search_user(username, password)

        if user:
            self._current_user = user
            self._is_authenticated = True
            self._error_message = ""
            return True
        else:
            self._current_user = None
            self._is_authenticated = False
            self._error_message = "Invalid login or password"
            return False

    def logout(self):
        self._current_user = None
        self._is_authenticated = False
        self._error_message = ""