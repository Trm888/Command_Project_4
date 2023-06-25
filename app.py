import logging
import time

import telegram
from environs import Env
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, LabeledPrice
from telegram import Update, BotCommand
from telegram.ext import Updater, ConversationHandler, CommandHandler, CallbackQueryHandler, CallbackContext, \
    MessageHandler, Filters, PreCheckoutQueryHandler

from check_name import FullNameCheck
from orm_functions import register_user, get_users, get_events_from_db, get_event_program, get_speakers_from_db, \
    get_current_user, get_current_speaker, create_question, get_contacts_from_db, get_updated_contacts


def main():
    env = Env()
    env.read_env()
    bot_token = env.str('TG_TOKEN')
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    payment_token = env.str('PAYMENT_TOKEN')

    CHOOSING_SPEAKER = 1
    GETTING_QUESTION = 2
    GETTING_NAME = 3
    GETTING_BIO = 4

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    def set_bot_commands(bot_token):
        bot = telegram.Bot(token=bot_token)
        commands = [
            BotCommand(command="/start", description="Start the bot")
        ]
        bot.set_my_commands(commands)

    def error_handler(update: Update, context: CallbackContext):
        logger.exception(msg="Произошло исключение", exc_info=context.error)

    def start(update: Update, context: CallbackContext):
        tg_id = update.message.from_user.id
        registered_users = get_users()
        if tg_id in registered_users:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="<b>Похоже вы уже регистрировались?Посмотрите наши мероприятия\n</b>",
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton('Мероприятия', callback_data='get_events')]])
            )
            context.user_data['menu'] = 'start'
            return ConversationHandler.END
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="<b>Добро пожаловать, я бот-гид по мероприятиям.\n</b>"
                     "<b>Прежде чем начать, давайте пройдем короткую процедуру регистрации.\n</b>"
                     "<b>Укажите Имя и Фамилию</b>",
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=ReplyKeyboardRemove()
            )
            context.user_data['menu'] = 'start'
            return GETTING_NAME

    def get_name(update: Update, context: CallbackContext):
        check_name = FullNameCheck().check(update.message.text)
        if not check_name:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="<b>Пожалуйста, введите корректное имя и фамилию.\n</b>",
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=ReplyKeyboardRemove()
            )
            return GETTING_NAME
        else:
            tg_user_id = update.message.from_user.id
            tg_user_nickname = update.message.from_user.username
            context.user_data['full_name'] = update.message.text
            register_user(tg_user_nickname, tg_user_id, context.user_data['full_name'].split()[0],
                          context.user_data['full_name'].split()[1])
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="<b>Отлично, теперь можете получить список мероприятий</b>",
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton('Мероприятия', callback_data='get_events')]])
            )
            context.user_data['menu'] = 'get_name'
            return ConversationHandler.END

    def get_events(update: Update, context: CallbackContext):
        events = get_events_from_db()
        print(events)
        context.user_data['tg_user'] = update.callback_query.from_user.id
        events_buttons = [
            [InlineKeyboardButton(f'Мероприятие {event["title"]}', callback_data=f'event_{event["id"]}')]
            for event in events]
        update.callback_query.edit_message_text(
            "<b>Выберите мероприятие, которое вас интересует.\n</b>",
            parse_mode=telegram.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(events_buttons, one_time_keyboard=True)
        )
        context.user_data['menu'] = 'get_events'

    def event_meny(update: Update, context: CallbackContext):
        start_button = [
            [InlineKeyboardButton('1. Получить программу мероприятия', callback_data='get_program')],
            [InlineKeyboardButton('2. Пообщаться с другими посетителями', callback_data='chat')],
            [InlineKeyboardButton('3. Задонатить организатору', callback_data='donate')],
            [InlineKeyboardButton('Назад', callback_data='back')]
        ]
        if not update.callback_query:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Добро пожаловать на мероприятие.\n"
                     "Вы можете получить программу мероприятия и задать вопросы выступающим,\n"
                     " пообщаться с другими участниками а также сделать донат организаторам.\n",
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(start_button, one_time_keyboard=True)
            )
            context.user_data['menu'] = 'event_meny'
        else:
            if context.user_data['menu'] == 'get_events':
                context.user_data['event_id'] = update.callback_query.data.split('_')[1]
            update.callback_query.edit_message_text(
                "Добро пожаловать на мероприятие.\n"
                "Вы можете получить программу мероприятия и задать вопросы выступающим,\n"
                " пообщаться с другими участниками а также сделать донат организаторам.\n",
                reply_markup=InlineKeyboardMarkup(start_button, one_time_keyboard=True)
            )
            context.user_data['menu'] = 'event_meny'

    def get_program(update, context):
        back_button = [[InlineKeyboardButton('Задать вопрос спикеру', callback_data='ask_question')],
                       [InlineKeyboardButton('Назад', callback_data='back')]]

        program = get_event_program(context.user_data['event_id'])
        formatted_program = "Программа мероприятия:\n"
        for speaker in program:
            start_time = speaker['start_time'].strftime("%H:%M")
            end_time = speaker['end_time'].strftime("%H:%M")
            speaker = f'{speaker["speaker__firstname"]} {speaker["speaker__secondname"]}'
            formatted_program += f"{start_time} - {end_time} --- {speaker}\n"

        update.callback_query.edit_message_text(
            formatted_program,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(back_button, one_time_keyboard=True))
        context.user_data['menu'] = 'get_program'

    def choose_speaker(update, context):
        speakers = get_speakers_from_db(context.user_data['event_id'])
        print(speakers)
        buttons = [[InlineKeyboardButton(f'Спикер {speaker["speaker__firstname"]} {speaker["speaker__secondname"]}',
                                         callback_data=f'speaker_{speaker["speaker__chat_id"]}')] for speaker in
                   speakers]
        buttons.append([InlineKeyboardButton('Назад', callback_data='back')])

        update.callback_query.edit_message_text(
            "Выберете спикера, которому хотите задать вопрос:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons, one_time_keyboard=True))
        context.user_data['menu'] = 'choose_speaker'
        return CHOOSING_SPEAKER

    def get_question(update, context):
        update.callback_query.edit_message_text(
            "Введите вопрос:",
            parse_mode="HTML")
        context.user_data['menu'] = 'get_question'
        context.user_data['selected_speaker'] = update.callback_query.data
        return GETTING_QUESTION

    def send_question(update, context):
        if context.user_data['menu'] == 'get_question':
            context.user_data['question'] = update.message.text
            current_user = get_current_user(update.message.from_user.id)
            current_speaker = get_current_speaker(context.user_data['selected_speaker'].split('_')[1])
            create_question(current_user, current_speaker, context.user_data['question'])
            update.message.reply_text("Ваш вопрос отправлен спикеру", parse_mode="HTML")
            quest_dict = {'Спикер': context.user_data['selected_speaker'], 'Вопрос': context.user_data['question']}
            print(quest_dict)
            context.user_data['menu'] = 'send_question'
            time.sleep(1)
            event_meny(update, context)
            return ConversationHandler.END

    def back_to_menu(update, context):
        menu = context.user_data.get('menu')
        if menu == 'event_meny':
            get_events(update, context)
        elif menu == 'get_program':
            event_meny(update, context)
        elif menu == 'choose_speaker':
            get_program(update, context)
        elif menu == 'get_donate':
            event_meny(update, context)
        elif menu == 'get_communication':
            event_meny(update, context)
            return ConversationHandler.END
        elif menu == 'get_sum':
            event_meny(update, context)

    def get_sum_for_donate(update, context):
        back_button = [[InlineKeyboardButton('Назад', callback_data='back')]]
        update.callback_query.edit_message_text(
            "Введите сумму которую хотите пожертвовать",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(back_button, one_time_keyboard=True))
        context.user_data['menu'] = 'get_sum'

    def get_donate(update, context, payment_token=payment_token):
        if context.user_data['menu'] == 'get_sum':
            amount = update.message.text
            if not amount.isdigit():
                update.message.reply_text('Введите число')
            else:
                context.user_data['sum'] = int(amount) * 100
                context.bot.send_invoice(
                    chat_id=update.effective_chat.id,
                    title='Donation',
                    description='Donation for event',
                    payload='some-invoice-payload-for-our-internal-use',
                    provider_token=payment_token,
                    start_parameter='test-payment',
                    currency='rub',
                    prices=[LabeledPrice('Donation', context.user_data['sum'])]
                )
                context.user_data['menu'] = 'get_donate'

    def precheckout_callback(update: Update, context: CallbackContext):
        query = update.pre_checkout_query
        query.answer(ok=True)

    def successful_payment_callback(update: Update, context: CallbackContext):
        context.bot.send_message(update.effective_chat.id, "Спасибо за пожертвование!")
        time.sleep(1)
        event_meny(update, context)

    def get_communication(update, context):
        user_business_card = get_current_user(update.callback_query.from_user.id).business_card
        if not user_business_card:
            back_button = [[InlineKeyboardButton('Назад', callback_data='back')]]
            update.callback_query.edit_message_text(
                "Прежде чем начать общение, пожалуйста расскажите о себе:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(back_button, one_time_keyboard=True)
            )
            context.user_data['menu'] = 'get_communication'
            return GETTING_BIO
        else:
            get_bio(update, context)

    def get_bio(update, context):
        tg_user_id = context.user_data['tg_user']
        user_business_card = get_current_user(tg_user_id).business_card
        if not user_business_card:
            context.user_data['bio'] = update.message.text
            get_updated_contacts(tg_user_id, context.user_data['bio'])
            contact_button = [[InlineKeyboardButton('Получить контакты', callback_data='get_contacts')]]
            update.message.reply_text(
                "Отлично! Теперь можете запросить контакты участников, которые вам интересны:",
                parse_mode="HTML", reply_markup=InlineKeyboardMarkup(contact_button))
            context.user_data['menu'] = 'get_bio'

            return ConversationHandler.END
        else:
            contact_button = [[InlineKeyboardButton('Получить контакты', callback_data='get_contacts')]]

            update.callback_query.edit_message_text(
                "Отлично! Теперь можете запросить контакты участников, которые вам интересны:",
                parse_mode="HTML", reply_markup=InlineKeyboardMarkup(contact_button))
            context.user_data['menu'] = 'get_bio'

    def get_contacts(update, context):
        user_nick_name = update.effective_chat.username
        print(user_nick_name)
        contacts = get_contacts_from_db()
        context.user_data['contacts'] = contacts
        context.user_data['contact_index'] = 0
        send_contact(update, context)

    def send_contact(update: Update, context: CallbackContext):
        contacts = context.user_data['contacts']
        contact_index = context.user_data['contact_index']
        current_contact = contacts[contact_index]
        update.callback_query.edit_message_text(
            f"Никнэйм в Telegram: <b>@{current_contact['username']}</b>\n"
            f"О себе: <b>{current_contact['business_card']}</b>",
            parse_mode=telegram.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('Следующий контакт', callback_data='next_contact')]])
        )

    def next_contact(update: Update, context: CallbackContext):
        contacts = context.user_data['contacts']
        contact_index = context.user_data['contact_index']
        if contact_index < len(contacts) - 1:
            context.user_data['contact_index'] += 1
        else:
            context.user_data['contact_index'] = 0
        send_contact(update, context)

    try:

        quest_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(choose_speaker, pattern='ask_question')],
            states={
                CHOOSING_SPEAKER: [CallbackQueryHandler(get_question, pattern=r'^speaker_\d+$')],
                GETTING_QUESTION: [MessageHandler(Filters.text, send_question)]
            },
            fallbacks=[CommandHandler('start', start)]
        )
        reg_conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                GETTING_NAME: [MessageHandler(Filters.text & ~ Filters.command, get_name)]},
            fallbacks=[]
        )

        reg_bio_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(get_communication, pattern='chat')],
            states={GETTING_BIO: [MessageHandler(Filters.text & ~ Filters.command, get_bio)]},
            fallbacks=[CallbackQueryHandler(back_to_menu, pattern='back')]
        )
        dp.add_error_handler(error_handler)
        dp.add_handler(reg_conv_handler)
        dp.add_handler(CallbackQueryHandler(get_events, pattern='get_events'))
        dp.add_handler(quest_conv_handler)
        dp.add_handler(reg_bio_conv_handler)
        dp.add_handler(CallbackQueryHandler(event_meny, pattern=r'^event_\d+$'))
        dp.add_handler(CallbackQueryHandler(get_program, pattern='get_program'))
        dp.add_handler(CallbackQueryHandler(back_to_menu, pattern='back'))
        dp.add_handler(CallbackQueryHandler(get_contacts, pattern='get_contacts'))
        dp.add_handler(CallbackQueryHandler(next_contact, pattern='next_contact'))
        dp.add_handler(CallbackQueryHandler(get_sum_for_donate, pattern='donate'))
        dp.add_handler(MessageHandler(Filters.text & ~ Filters.command, get_donate))
        dp.add_handler(PreCheckoutQueryHandler(precheckout_callback))
        dp.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))
        set_bot_commands(bot_token)

        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.exception("Unhandled exception: %s", str(e))


if __name__ == '__main__':
    main()
