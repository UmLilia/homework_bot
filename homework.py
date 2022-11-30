import os
import sys
import time
import logging
import requests

import telegram

from dotenv import load_dotenv

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


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='error.log',
    filemode='w',
    level=logging.DEBUG
)
print(logging.info)

def logger_error(message_error):
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    bot.send_message(TELEGRAM_CHAT_ID, message_error)
    return logging.error(message_error)

def check_tokens():
    """Проверяет доступность переменных окружения"""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    filtered = (list(filter(None,tokens)))
    if len(filtered) != len(tokens):
        logging.critical('Отсутствует обязательная переменная окружения.'
        'Программа принудительно остановлена.')
        return False
    else:
        return True

def send_message(bot, message):
    """Отправляет сообщение в Telegram чат"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger_error(f'Сбой при отправке сообщения - {error}')
    else:
        logging.debug(f'удачная отправка сообщения: {message}')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса"""
    try:
        response = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params={'from_date':current_timestamp}
    )
    except Exception as error:
        logger_error(f'Сбой при запросе к эндпоинту - {error}')
    if response.status_code != 200:
        raise Exception(f'Недоступность эндпоинта {ENDPOINT}')
    else:
        return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации"""
    if not isinstance(response, dict):
        raise TypeError('получен неверный тип данных')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('получен неверный тип данных')
    return homeworks


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы"""
    if 'homework_name' not in homework:
        raise KeyError('в ответе API нет ключа homework_name')
    if 'status' not in homework:
        raise Exception('в ответе API нет ключа status')
    status = homework.get('status')
    homework_name = homework.get('homework_name')
    if status not in HOMEWORK_VERDICTS:
        raise Exception(f'неожиданный статус домашней работы - {status}')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    if check_tokens() == False:
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
                logging.debug(f'отсутствие в ответе новых статусов')
        except Exception as error:
            last_error = ''
            message_error = (f'Сбой в работе программы: {error}')
            logging.error(message_error)
            if str(last_error) != str(error):
                send_message(bot, message_error)
                last_error = error
        time.sleep(RETRY_PERIOD)

if __name__ == '__main__':
    main()
