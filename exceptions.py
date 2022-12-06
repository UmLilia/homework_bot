class ApiAnswerError(Exception):
    """Класс исключения при запросе API."""


class HTTPStatusError(Exception):
    """Класс исключения при недоступности API."""


class ResponseWithoutKeyError(Exception):
    """Класс исключения при отсутствии необходимого ключа."""


class HomeWorkStatusError(Exception):
    """Класс исключения при неожиданном статусе работы."""
