#  meetup_storage
Клиентская часть проекта meetup_storage
Бот для хранения информации о митапах, позволяет получать информацию о митапах по запросу.


## Запуск

- Скачайте код. Установите зависимости:
```sh
pip install -r requirements.txt
```
Выполнить миграцию: 
```sh
python3 manage.py migrate`
```
Создайте файл с переменными окружения ".env", разместите его в той же директории, где и файл app.py, запишите туда данные в таком формате: ПЕРЕМЕННАЯ=значение.

TG_TOKEN - токен телеграм бота, инструкция по созданию бота: https://medium.com/spidernitt/how-to-create-your-own-telegram-bot-63d1097999b6

PAYMENT_TOKEN - токен для оплаты через телеграм.

Требуется подключить оплату в настройках бота в BotFather. Инструкция: https://core.telegram.org/bots/payments#getting-a-token
