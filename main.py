import attr
import telebot
import json
from attrs import define
from telebot import types
from datetime import datetime
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
    states: str = ''
    is_open: bool = True
    post_number: int = 1
    time: datetime = attr.field(factory=datetime.now)
    brigadier: str = ''
    num_session: int = 0
    post_statuses: list[str] = attr.field(factory=list)  # ####################
    comment: str = ''


@define
class SessionClose:
    states: str = ''
    num_session: int = 1
    brigadier: str = ''
    lot: str = ''
    details: dict = attr.ib(factory=dict)
    details_prep: dict = attr.ib(factory=dict)
    pallets: int = 0
    cement: int = 0
    perlite: int = 0
    line_comment: str = ''
    brigade_comment: str = ''

    def __attrs_post_init__(self):
        # Инициализируем словарь деталей по умолчанию
        self.details = {
            'АП-9': 0,
            'АП-12': 0,
            'Ва-9': 0,
            'ВА-12': 0
        }
        self.details_prep = {
            'АП-9': 0,
            'АП-12': 0,
            'Ва-9': 0,
            'ВА-12': 0
        }


sessions = {}
sessions_close = {}


def get_session(user_id):
    # Если объект Session для данного пользователя уже существует, возвращаем его
    if user_id in sessions and sessions[user_id].states != 'stopped':
        return sessions[user_id]
    elif user_id in sessions and sessions[user_id].states == 'stopped':
        sessions[user_id].states = ''
        get_help(user_id)
    else:
        sessions[user_id] = Session()
        return sessions[user_id]


def get_help(user_id):
    bot.send_message(user_id, "Какую процедуру запустим?"
                              "\n\n/open - Открытие смены  "
                              "\n\n/close - Закрытие смены "
                              "\n\n/workers - Журлан работников", reply_markup=types.ReplyKeyboardRemove())


def delete_session(user_id):
    if user_id in sessions:
        del sessions[user_id]


def get_session_close(user_id):
    # Если объект Session для данного пользователя уже существует, возвращаем его
    if user_id in sessions_close:
        return sessions_close[user_id]
    # Если объект Session для данного пользователя не существует, создаем его и возвращаем
    else:
        sessions_close[user_id] = SessionClose()
        return sessions_close[user_id]


def delete_session_close(user_id):
    if user_id in sessions_close:
        del sessions_close[user_id]


# Создаем клавиатуру с кнопками "да" и "нет"
markup_yes_no = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
markup_yes_no.add("🟢", "🔴", "Начать сначала")

# Создаем клавиатуру с кнопками "Первая" и "Вторая"
markup_one_two = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
markup_one_two.add("Первая", "Вторая", "Начать сначала")

# Создаем клавиатуру с произведенными деталями
markup_details = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
markup_details.add("АП-9", "АП-12", "Ва-9", "ВА-12", "Далее", "Начать сначала")

# Создаем клавиатуру с бригадирами
markup_who_open = types.InlineKeyboardMarkup()
item1 = types.InlineKeyboardButton("Гроссу Е. А.", callback_data="Гроссу Е. А.")
item2 = types.InlineKeyboardButton("Князев В. К.", callback_data="Князев В. К.")
item3 = types.InlineKeyboardButton("Другой...", callback_data="Другой...")
markup_who_open.add(item1, item2, item3)

markup_who_close = types.InlineKeyboardMarkup()
item1 = types.InlineKeyboardButton("Гроссу Е. А. ", callback_data="Гроссу Е. А. ")
item2 = types.InlineKeyboardButton("Князев В. К. ", callback_data="Князев В. К. ")
item3 = types.InlineKeyboardButton("Другой. . .", callback_data="Другой. . .")
markup_who_close.add(item1, item2, item3)


# @bot.message_handler(commands=['stop'])
# def stop(message):
#     try:
#         sessions[message.chat.id].states = 'stopped'
#         sessions_close[message.chat.id].states = 'stopped'
#     except Exception:
#         get_help[message.chat.id)


@bot.message_handler(commands=['start'])
def open_shift(message):
    bot.send_message(message.chat.id, "Привет. Я помогу автоматизировать процесс фиксирования важной для "
                                      "производства информациии. Мной не сложно пользоваться. Главное придерживайся "
                                      "инструкции и лишний раз не запускай их без надобности. Запись в конечную таблицу"
                                      " не произойдет, пока мы не закончим цикл, поэтому смело можешь нажимать и писать"
                                      " мне что угодно, ты ничего не сломаешь, и лучше  сможешь понять "
                                      "как я работаю и не бояться, что что-то пойдет не по плану. "
                                      "В конце каждой процедуры я попрошу подтвердить отчет, который мы с тобой "
                                      "собрали, что бы избежать ошибок в отчете, и ты сам перепроверишь, правильно ли "
                                      "все записано или его надо переделать. Если будут какие-то "
                                      "недопонимания - я сообщую. Постарайся не бросать процесс на пол пути,"
                                      "а если все таки надо отменить  Я покажу тебе список команд, нажимай по ссылкам")
    get_help(message.chat.id)


@bot.message_handler(commands=['open'])
def open_shift(message):
    bot.send_message(message.chat.id, "Кто открывает смену?", reply_markup=markup_who_open)


@bot.callback_query_handler(func=lambda call: True)
def check_name(call):
    session = get_session(call.message.chat.id)
    session_close = get_session_close(call.message.chat.id)
    if call.data in ["Гроссу Е. А.", "Князев В. К."]:
        delete_session_close(call.message.chat.id)
        bot.send_message(call.message.chat.id, f"Смену открывает {call.data}.")
        session.brigadier = call.data
        bot.send_message(call.message.chat.id, "Какая смена❓", reply_markup=markup_one_two)
        bot.register_next_step_handler(call.message, check_num_session)
    elif call.data == "Другой...":
        delete_session_close(call.message.chat.id)
        bot.send_message(call.message.chat.id, "Кто открывает?", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(call.message, get_name)
    elif call.data in ["Гроссу Е. А. ", "Князев В. К. "]:
        delete_session(call.message.chat.id)
        bot.send_message(call.message.chat.id,
                         f"Смену закрывает {call.data}.", reply_markup=types.ReplyKeyboardRemove())
        session_close.brigadier = call.data
        bot.send_message(call.message.chat.id, "Какая смена❓", reply_markup=markup_one_two)
        bot.register_next_step_handler(call.message, check_num_session_close)
    elif call.data == "Другой. . .":
        delete_session(call.message.chat.id)
        bot.send_message(call.message.chat.id, "Кто закрывает?", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(call.message, get_name_close)


def get_name(message):
    session = get_session(message.chat.id)
    session.brigadier = message.text
    bot.send_message(message.chat.id, f"Cмену открывает {message.text}.")
    bot.send_message(message.chat.id, "Какая смена❓", reply_markup=markup_one_two)
    bot.register_next_step_handler(message, check_num_session)


def check_num_session(message):
    session = get_session(message.chat.id)
    if message.text == 'Начать сначала':
        delete_session(message.chat.id)
        get_help(message.chat.id)
    elif message.text == 'Первая' or message.text == '1':
        session.num_session = 1
        check_post(message, 1)
    elif message.text == 'Вторая' or message.text == '2':
        session.num_session = 2
        check_post(message, 1)


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
    if message.text == 'Начать сначала':
        delete_session(message.chat.id)
        get_help(message.chat.id)
    elif message.text == "🔴":
        bot.send_message(message.chat.id, "Коментарий:", reply_markup=None)
        bot.register_next_step_handler(message, get_comment)
    elif message.text == "🟢":
        bot.send_message(message.chat.id, f"🟢 Пост {session.post_number}")
        session.post_statuses.append("🟢")
        if session.post_number == 8:
            session.post_number = 1
            bot.register_next_step_handler(message, append_session)
            append_session(message)
        else:
            session.post_number += 1
            check_post(message, session.post_number)
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
        bot.register_next_step_handler(message, append_session)
        append_session(message)


def append_session(message):
    user_id = message.chat.id
    session = get_session(user_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.time = now
    try:
        bot.send_message(kera_id, f'{session.time}\n {session.num_session}-я смена\n Бригадир: {session.brigadier}'
                                  f'\n\n Поддоны: {session.post_statuses[0]}\n Торцовка: {session.post_statuses[1]}'
                                  f'\n Пакетирование: {session.post_statuses[2]}\n Формовка: {session.post_statuses[3]}'
                                  f'\n Мешалка: {session.post_statuses[4]}\n Распределитель: {session.post_statuses[5]}'
                                  f'\n Химия: {session.post_statuses[6]}\n Перлит: {session.post_statuses[7]}')
        bot.send_message(message.chat.id, f"Смена открыта.", reply_markup=types.ReplyKeyboardRemove())
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheetId,
            valueInputOption="USER_ENTERED",
            range="Открытие Смены!B:B",
            body={"values": [[session.time, session.num_session, session.brigadier, None,
                              *session.post_statuses[:8], None, None]]}
        ).execute()
    except Exception as exx:
        bot.send_message(user_id, exx)
    delete_session(user_id)
    # https://docs.google.com/spreadsheets/d/1ufeRhZB-8aUAxd2KE-7OGVrJU9zbq22UEA4y7mGZul4/edit#gid=0


#######################################################################################################################
#######################################################################################################################


@bot.message_handler(commands=['close'])
def close_shift(message):
    bot.send_message(message.chat.id, "Кто закрывает смену?", reply_markup=markup_who_close)


def get_name_close(message):
    session_close = get_session_close(message.chat.id)
    session_close.brigadier = message.text
    bot.send_message(message.chat.id, f"Cмену закрывает {message.text}.")
    bot.send_message(message.chat.id, "Какая смена❓", reply_markup=markup_one_two)
    bot.register_next_step_handler(message, check_num_session_close)


def check_num_session_close(message):
    session_close = get_session_close(message.chat.id)
    if message.text == 'Начать сначала':
        delete_session_close(message.chat.id)
        get_help(message.chat.id)
    elif message.text == 'Первая' or message.text == '1':
        session_close.num_session = 1
        bot.send_message(message.chat.id, "Номер партии:",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_lot)
    elif message.text == 'Вторая' or message.text == '2':
        session_close.num_session = 2
        bot.send_message(message.chat.id, "Номер партии:",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_lot)
    else:
        bot.send_message(message.chat.id, "Придерживайся скрипта. Какую смену открываем? ",
                         reply_markup=markup_one_two)
        bot.register_next_step_handler(message, check_num_session_close)


def get_lot(message):
    session_close = get_session_close(message.chat.id)
    if message.text == 'Начать сначала':
        delete_session_close(message.chat.id)
        get_help(message.chat.id)
    else:
        session_close.lot = message.text
        bot.send_message(message.chat.id, "Теперь давай запишем, сколько панелей каждого вида было наформовано "
                                          "за смену.",
                         reply_markup=markup_details)
        bot.register_next_step_handler(message, get_details)


def get_details(message):
    detail = message.text
    session_close = get_session_close(message.chat.id)
    if message.text == 'Начать сначала':
        delete_session_close(message.chat.id)
        get_help(message.chat.id)
    elif detail == 'Далее':
        bot.send_message(message.chat.id, "Теперь давай запишем, сколько панелей каждого вида было наторцовано "
                                          "за смену.",
                         reply_markup=markup_details)
        bot.register_next_step_handler(message, get_details_pre)
    elif detail in session_close.details:
        bot.send_message(message.chat.id, f"Кол-во наформованных {detail}: ",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_detail_count, detail)


def get_details_pre(message):
    detail = message.text
    if message.text == 'Начать сначала':
        delete_session_close(message.chat.id)
        get_help(message.chat.id)
    elif detail == 'Далее':
        get_pallets(message)
    else:
        bot.send_message(message.chat.id, f"Кол-во наторцованных {detail}: ",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_detail_pre_count, detail)


# Обработчик ввода количества деталей
def get_detail_count(message, detail):
    session_close = get_session_close(message.chat.id)
    try:
        count = int(message.text)
        session_close.details[detail] = count
        bot.send_message(message.chat.id,
                         f"{detail} наформовано {session_close.details[detail]}. "
                         f"Выбери следующую панель или напиши 'Далее'.",
                         reply_markup=markup_details)
        bot.register_next_step_handler(message, get_details)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число.",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_detail_count, detail)


def get_detail_pre_count(message, detail):
    session_close = get_session_close(message.chat.id)
    try:
        count = int(message.text)
        session_close.details_prep[detail] = count
        bot.send_message(message.chat.id,
                         f"{detail} наторцовано {session_close.details_prep[detail]}. "
                         f"Выбери следующую панель или напиши 'Далее'.",
                         reply_markup=markup_details)
        bot.register_next_step_handler(message, get_details_pre)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число.",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_detail_pre_count, detail)


def get_pallets(message):
    bot.send_message(message.chat.id, "Сколько поддонов сбито? ", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_cement)


def get_cement(message):
    session_close = get_session_close(message.chat.id)
    try:
        session_close.pallets = int(message.text)
        bot.send_message(message.chat.id, "Сколько цемента израсходовано?", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_perlite)
    except ValueError:
        bot.send_message(message.chat.id, "Я могу записать только число. Давай попробуем еще раз."
                                          "\n\nСколько поддонов сбито?", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_cement)


def get_perlite(message):
    session_close = get_session_close(message.chat.id)
    try:
        session_close.cement = message.text
        bot.send_message(message.chat.id, "Сколько перлита израсходовано?",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_line_comment)
    except ValueError:
        bot.send_message(message.chat.id, "Я могу записать только число. Давай попробуем еще раз."
                                          "\n\nСколько цемента израсходовано?",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_perlite)


def get_line_comment(message):
    session_close = get_session_close(message.chat.id)
    try:
        session_close.perlite = message.text
        bot.send_message(message.chat.id, f"Комментарий по линии?", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_brigade_comment)
    except ValueError:
        bot.send_message(message.chat.id, "Я могу записать только число. Давай попробуем еще раз."
                                          "\n\nСколько цемента израсходовано?",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_line_comment)


def get_brigade_comment(message):
    session_close = get_session_close(message.chat.id)
    session_close.line_comment = message.text
    bot.send_message(message.chat.id, f"Комментарий по работе бригады?")
    bot.register_next_step_handler(message, append_session_close)


def append_session_close(message):
    user_id = message.chat.id
    session_close = get_session_close(user_id)
    session_close.brigade_comment = message.text
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bot.send_message(arm_id,
                         f'{now}\n {session_close.num_session}-я смена'
                              f'\nБригадир: {session_close.brigadier}'
                              f'\n\nНомер партии: {session_close.lot}'
                              f'\n\n  Формовка:'
                              f'\n     АП-9: {session_close.details['АП-9']}'
                              f'\n     АП-12: {session_close.details['АП-12']}'
                              f'\n     Ва-9: {session_close.details['Ва-9']}'
                              f'\n     ВА-12: {session_close.details['ВА-12']}'
                              f'\n\n  Торцовка:'
                              f'\n     АП-9: {session_close.details_prep['АП-9']}'
                              f'\n     АП-12: {session_close.details_prep['АП-12']}'
                              f'\n     Ва-9: {session_close.details_prep['Ва-9']}'
                              f'\n     ВА-12: {session_close.details_prep['ВА-12']}'
                              f'\n\nПоддонов сбито: {session_close.pallets}'
                              f'\nЦемента израсходовано: {session_close.cement}'
                              f'\nПерлита израсходовано {session_close.perlite}'
                              f'\nКоментарий по линии: {session_close.line_comment}'
                              f'\nКомментарий по бригаде: {session_close.brigade_comment}')
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheetId,
        valueInputOption="USER_ENTERED",
        range="Закрытие Смены!A2",
        body={"values": [[session_close.time, session_close.num_session, session_close.brigadier, None,
                          session_close.lot, session_close.details['АП-9'], session_close.details['АП-12'],
                          session_close.details['Ва-9'], session_close.details['ВА-12'],
                          session_close.details_prep['АП-9'], session_close.details_prep['АП-12'],
                          session_close.details_prep['Ва-9'], session_close.details_prep['ВА-12'],
                          session_close.cement, session_close.perlite, session_close.pallets,
                          session_close.line_comment, session_close.brigade_comment]]}
    ).execute()
    delete_session_close(user_id)
    get_help(user_id)


def main():
    while True:
        try:
            bot.polling(non_stop=True, interval=0)
        except Exception:
            time.sleep(0.1)
            continue


if __name__ == '__main__':
    main()
