import attr
import telebot
import json
from attrs import define
from telebot import types
from datetime import datetime
import schedule
import time
import httplib2
import googleapiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

kera_id = 314168780
arm_id = "-1001970375444_13"
with open('auth2.txt', 'r') as file:
    data = json.load(file)

# Присваиваем переменной ID значение spreadsheetId
spreadsheetId = data['spreadsheetId']
telebot_api = data['telebot_api']

bot = telebot.TeleBot(telebot_api)

CREDENTIALS_FILE = 'auth2.txt'  # Имя файла с закрытым ключом, вы должны подставить свое
# Читаем ключи из файла
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                               ['https://www.googleapis.com/auth/spreadsheets',
                                                                'https://www.googleapis.com/auth/drive'])

httpAuth = credentials.authorize(httplib2.Http())  # Авторизуемся в системе
service = googleapiclient.discovery.build('sheets', 'v4', http=httpAuth)  # Выбираем работу с таблицами и 4 версию API


@define
class Session:
    # user_data: list[str]
    post_number: int = 1
    post_statuses: list[str] = attr.field(factory=list)  # ####################
    time: datetime = attr.field(factory=datetime.now)
    num_session: int = 0
    brigadier: str = ''
    line_comment: str = ''
    brigade_comment: str = ''


sessions = {}


def get_session(user_id):
    # Если объект Session для данного пользователя уже существует, возвращаем его
    if user_id in sessions:
        return sessions[user_id]
    # Если объект Session для данного пользователя не существует, создаем его и возвращаем
    else:
        sessions[user_id] = Session()
        return sessions[user_id]


def delete_session(user_id):
    if user_id in sessions:
        del sessions[user_id]


# Создаем клавиатуру с кнопками "да" и "нет"
markup_yes_no = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
markup_yes_no.add("🟢", "🔴")

# Создаем клавиатуру с кнопками "Первая" и "Вторая"
markup_one_two = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
markup_one_two.add("Первая", "Вторая")

# Создаем клавиатуру с бригадирами
markup_who_open = types.InlineKeyboardMarkup()
item1 = types.InlineKeyboardButton("Гроссу Е. А.", callback_data="Гроссу Е. А.")
item2 = types.InlineKeyboardButton("Князев В. К.", callback_data="Князев В. К.")
item3 = types.InlineKeyboardButton("Другой...", callback_data="Другой...")
markup_who_open.add(item1, item2, item3)


@bot.message_handler(commands=['checklist'])
def open_shift(message):
    bot.send_message(message.chat.id, "Кто открывает смену?", reply_markup=markup_who_open)


@bot.message_handler(commands=['get_chat_id'])
def get_chat_id(message):
    bot.send_message(message.chat.id, f"{message.chat}")


@bot.callback_query_handler(func=lambda call: True)
def check_name(call):
    session = get_session(call.message.chat.id)
    if call.data in ["Гроссу Е. А.", "Князев В. К."]:
        bot.send_message(call.message.chat.id, f"Смену открывает {call.data}.")
        session.brigadier = call.data
        bot.send_message(call.message.chat.id, "Какая смена❓", reply_markup=markup_one_two)
        bot.register_next_step_handler(call.message, check_num_session)
    elif call.data == "Другой...":
        bot.send_message(call.message.chat.id, "Кто открывает?", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(call.message, get_name)


def get_name(message):
    session = get_session(message.chat.id)
    session.brigadier = message.text
    bot.send_message(message.chat.id, f"Cмену открывает {message.text}.")
    bot.send_message(message.chat.id, "Какая смена❓", reply_markup=markup_one_two)
    bot.register_next_step_handler(message, check_num_session)


def check_num_session(message):
    session = get_session(message.chat.id)
    if message.text == 'Первая' or message.text == '1':
        session.num_session = 1
        check_post(message, 1)
    elif message.text == 'Вторая' or message.text == '2':
        session.num_session = 2
        check_post(message, 1)
    else:
        bot.send_message(message.chat.id, "Придерживайся скрипта. Какую смену открываем? ", reply_markup=markup_one_two)
        bot.register_next_step_handler(message, check_num_session)


def check_post(message, post):
    post_names = {
        1: "Поддоны",
        2: "Торцовка",
        3: "Пакетирование",
        4: "Формовка",
        5: "Мешалка",
        6: "Распределитель",
        7: "Химия",
        8: "Перлит"
    }
    post_name = post_names.get(post, "Неизвестный пост")
    bot.send_message(message.chat.id, f"Пост {post_name}. \nЧисто?", reply_markup=markup_yes_no)
    bot.register_next_step_handler(message, check_post_status)


def check_post_status(message):
    session = get_session(message.chat.id)
    if message.text == "🔴":
        bot.send_message(message.chat.id, "Коментарий:", reply_markup=None)
        bot.register_next_step_handler(message, get_comment)
    elif message.text == "🟢":
        bot.send_message(message.chat.id, f"🟢 Пост {session.post_number}")
        session.post_statuses.append("🟢")
        if session.post_number < 8:
            session.post_number += 1
            check_post(message, session.post_number)
        else:
            session.post_number = 1
            get_line_comment(message)
    else:
        bot.send_message(message.chat.id, "Придерживайся скрипта. ", reply_markup=None)
        check_post(message, session.post_number)


def get_comment(message):
    session = get_session(message.chat.id)
    bot.send_message(message.chat.id, f"🔴 Пост {session.post_number} - {message.text}.")
    session.post_statuses.append(f"🔴 {message.text}")
    if session.post_number < 8:
        session.post_number += 1
        check_post(message, session.post_number)
    else:
        session.post_number = 1
        get_line_comment(message)


def get_line_comment(message):
    bot.send_message(message.chat.id, f"Комментарий по линии?", reply_markup=None)
    bot.register_next_step_handler(message, get_brigade_comment)


def get_brigade_comment(message):
    session = get_session(message.chat.id)
    session.line_comment = message.text
    bot.send_message(message.chat.id, f"Комментарий по работе бригады?")
    bot.register_next_step_handler(message, append_session)

def append_session(message):
    user_id = message.chat.id
    session = get_session(user_id)
    session.brigade_comment = message.text
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.time = now
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheetId,
        valueInputOption="USER_ENTERED",
        range="Лист1!B2",
        body={"values": [[session.time, session.num_session, session.brigadier, None,
                          *session.post_statuses[:8],
                          session.line_comment, session.brigade_comment]]}
    ).execute()
    bot.send_message(arm_id, f'{session.time}\n {session.num_session}-я смена\n Бригадир: {session.brigadier}'
                             f'\n\n Поддоны: {session.post_statuses[0]}\n Торцовка: {session.post_statuses[1]}'
                             f'\n Пакетирование: {session.post_statuses[2]}\n Формовка: {session.post_statuses[3]}'
                             f'\n Мешалка: {session.post_statuses[4]}\n Распределитель: {session.post_statuses[5]}'
                             f'\n Химия: {session.post_statuses[6]}\n Перлит: {session.post_statuses[7]}'
                             f'\n\n Комментарий по линии: {session.line_comment}'
                             f'\n Комментарий по бригаде: {session.brigade_comment}\n')
    bot.send_message(message.chat.id, f"Смена открыта.", reply_markup=types.ReplyKeyboardRemove())
    delete_session(user_id)
    # https://docs.google.com/spreadsheets/d/1ufeRhZB-8aUAxd2KE-7OGVrJU9zbq22UEA4y7mGZul4/edit#gid=0


def main():
    while True:
        try:
            bot.polling(non_stop=True, interval=0)
        except Exception:
            time.sleep(0.1)
            continue


if __name__ == '__main__':
    main()
