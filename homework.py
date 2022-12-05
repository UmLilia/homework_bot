import os
import sys
import time
import logging
import requests
import telegram

from dotenv import load_dotenv

from exceptions import MessageSendError, ApiAnswerError, HTTPStatusError, ResponseWithoutKeyError, HomeWorkStatusError

from http import HTTPStatus

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        message_error = (f'Сбой при отправке сообщения - {error}')
        logging.error(message_error)
        raise MessageSendError(message_error)
    else:
        logging.debug(f'удачная отправка сообщения: {message}')


def get_api_answer(current_timestamp) -> dict:
    """Делает запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': current_timestamp}
        )
    except Exception as error:
        message_error = (f'Сбой при запросе к эндпоинту - {error}')
        logging.error(message_error)
        raise ApiAnswerError(message_error)
    if response.status_code != HTTPStatus.OK:
        message_error = (f'Недоступность эндпоинта {ENDPOINT}')
        logging.error(message_error)
        raise HTTPStatusError(message_error)
    return response.json()


def check_response(response) -> list:
    """Проверяет ответ API на соответствие документации."""
    message_error = 'получен неверный тип данных'
    if not isinstance(response, dict):
        logging.error(message_error)
        raise TypeError(message_error)
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        logging.error(message_error)
        raise TypeError(message_error)
    return homeworks


def parse_status(homework) -> str:
    """Извлекает из информации о домашней работе статус этой работы."""
    if 'homework_name' not in homework:
        raise ResponseWithoutKeyError('в ответе API нет ключа homework_name')
    if 'status' not in homework:
        raise ResponseWithoutKeyError('в ответе API нет ключа status')
    status = homework.get('status')
    homework_name = homework.get('homework_name')
    if status not in HOMEWORK_VERDICTS:
        raise HomeWorkStatusError(f'неожиданный статус домашней работы - {status}')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error = ''
    if not check_tokens():
        logging.critical('Отсутствует обязательная переменная окружения.' 
                         'Программа принудительно остановлена.')
        sys.exit()
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date')
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logging.debug('отсутствие в ответе новых статусов')
        except Exception as error:
            message_error = (f'Сбой в работе программы: {error}')
            logging.error(message_error)
            if last_error != error:
                send_message(bot, message_error)
                last_error = error
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='error.log',
        filemode='w',
        level=logging.DEBUG
    )
    main()
