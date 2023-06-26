import os
import time
from datetime import date

import django
import telegram

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'storage.settings')

django.setup()

from db.models import User, Event, Question, Alert, Donation


def get_current_user(telegram_id):
    return User.objects.get(chat_id=telegram_id)


def get_current_speaker(speaker_id):
    return User.objects.get(chat_id=speaker_id)


def get_users():
    return User.objects.values_list('chat_id', flat=True)


def register_user(username, telegram_id, first_name, last_name):
    return User.objects.create(username=username, chat_id=telegram_id, firstname=first_name, secondname=last_name)


def get_events_from_db():
    today = date.today()
    return Event.objects.filter(date__gte=today).values('id', 'title')


def get_event_program(evnt_id):
    return Event.objects.get(id=evnt_id).speeches.all().values('start_time', 'end_time', 'speaker__firstname',
                                                               'speaker__secondname')


def get_speakers_from_db(evnt_id):
    return Event.objects.get(id=evnt_id).speeches.all().values('speaker__chat_id', 'speaker__firstname',
                                                               'speaker__secondname')


def create_question(from_who, to_who, text):
    return Question.objects.create(from_who=from_who, to_who=to_who, text=text)


def get_contacts_from_db():
    return User.objects.values('username', 'firstname', 'secondname', 'business_card')


def get_updated_contacts(telegram_id, business_card):
    return User.objects.filter(chat_id=telegram_id).update(business_card=business_card)


def create_donation(username, summ):
    return Donation.objects.create(user=username, summ=summ)


def start_polling_alerts(bot):
    while True:
        for alert in Alert.objects.all():
            for user in User.objects.all():
                try:
                    bot.send_message(user.chat_id, alert.text)
                except telegram.error.BadRequest as e:
                    # Обработка исключения, когда отправка сообщения не удалась
                    print(f"Не удалось отправить сообщение пользователю {user.chat_id}: {e}")
                    continue
                alert.delete()
        time.sleep(10)
