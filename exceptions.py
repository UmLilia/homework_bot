class MessageSendError(Exception):
    """Класс исключения при отправке сообщения."""
    pass


class ApiAnswerError(Exception):
    """Класс исключения при запросе API."""
    pass


class HTTPStatusError(Exception):
    """Класс исключения при недоступности API."""
    pass


class ResponseWithoutKeyError(Exception):
    """Класс исключения при отсутствии необходимого ключа."""
    pass


class HomeWorkStatusError(Exception):
    """Класс исключения при неожиданном статусе работы."""
    pass