import datetime as dt
import sqlite3
from random import randint

import telebot
from telebot import types

from JOKES import JOKES

token = '<TOKEN>'
bot = telebot.TeleBot(token)

CODE = None
PASSWORD = None
ADMIN_PASSWORD = None
ID = None

LESSON_TITLE = None
HOMEWORK = None
DATE = None


@bot.message_handler(commands=['start'])
def start_message(message):
    db_add_user(message=message)
    bot.send_message(message.chat.id, 'Добро пожаловать в ДЗ БОТ')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Войти в комнату")
    item2 = types.KeyboardButton('Создать комнату')
    markup.add(item1)
    markup.add(item2)
    bot.send_message(message.chat.id, 'Войдите или зарегистрируйтесь', reply_markup=markup)


@bot.message_handler(commands=['button'])
def button_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Кнопка")
    item2 = types.KeyboardButton('Регистрация')
    markup.add(item1)
    markup.add(item2)
    bot.send_message(message.chat.id, 'Выберите что вам надо', reply_markup=markup)


@bot.message_handler(content_types='text')
def message_reply(message):
    if message.text == "Войти в комнату":
        bot.send_message(message.chat.id, "Введите код комнаты:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, sign_in_code)
    if message.text == "Создать комнату":
        bot.send_message(message.chat.id, "Придумайте код комнаты:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, log_in_title)


@bot.message_handler(content_types='text')
def sign_in_code(message):
    global CODE
    CODE = message.text
    print(message.text)
    bot.send_message(message.chat.id, 'Введите пароль комнаты:')

    bot.register_next_step_handler(message, sign_in_password)


@bot.message_handler(content_types='text')
def sign_in_password(message):
    global PASSWORD, ID, ADMIN_PASSWORD
    PASSWORD = message.text
    print(message.text)
    res = db()
    if res:
        bot.send_message(message.chat.id, 'Добро пожаловать!!!')
        main_window(message)
        ID = res[0][0]
        ADMIN_PASSWORD = res[0][-1]
        # bot.register_next_step_handler(message, main_window)
    else:
        bot.send_message(message.chat.id, 'Что-то пошло не так!\nНеверный пароль или код.')


@bot.message_handler(content_types='text')
def log_in_title(message):
    global CODE
    print(message.text)
    CODE = message.text
    if db_ne_znayu():
        bot.send_message(message.chat.id, 'Код сохранён!')
        bot.send_message(message.chat.id, 'Придумайте пароль:')
        bot.register_next_step_handler(message, log_in_password)
    else:
        bot.send_message(message.chat.id, 'Данный код уже есть\nПридумайте другой')
        start_message(message)


@bot.message_handler(content_types='text')
def log_in_password(message):
    global PASSWORD
    bot.send_message(message.chat.id, 'Пароль сохранён!')
    bot.send_message(message.chat.id, 'Придумайте код администратора:')
    print(message.text)
    PASSWORD = message.text
    bot.register_next_step_handler(message, log_in_admin_code)


@bot.message_handler(content_types='text')
def log_in_admin_code(message):
    print(message.text)
    global ADMIN_PASSWORD, ID
    ADMIN_PASSWORD = message.text
    bot.send_message(message.chat.id, 'Код админа сохранён!')
    db_create()
    bot.send_message(message.chat.id, 'Поздравляем вы создали комнату!!!')
    ID = db()[0][0]
    main_window(message)


@bot.message_handler(content_types='text')
def main_window(message):
    STATUS = db_status(message)
    if STATUS == 'Пользователь':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Получить ДЗ🎓")
        item2 = types.KeyboardButton('Расскажи анекдот🤣')
        item3 = types.KeyboardButton('Стать админом👑')
        markup.add(item1, item2)
        markup.add(item3)
        bot.send_message(message.chat.id, 'Выбирите:', reply_markup=markup)
        bot.register_next_step_handler(message, main_window_but)

    elif STATUS == 'Админ':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Получить ДЗ🎓")
        item2 = types.KeyboardButton('Расскажи анекдот🤣')
        item3 = types.KeyboardButton('Добавить задание📝')
        markup.add(item1, item2)
        markup.add(item3)
        bot.send_message(message.chat.id, 'Выберете:', reply_markup=markup)
        bot.register_next_step_handler(message, main_window_but)


@bot.message_handler(content_types='text')
def main_window_but(message):
    if message.text == 'Расскажи анекдот🤣':
        bot.send_message(message.chat.id, JOKES[randint(0, len(JOKES) - 1)])
        main_window(message)
    if message.text == 'Получить ДЗ🎓':
        bot.send_message(message.chat.id, 'Актуальное домашнее задание:')
        homeworks = db_search_homework()
        lst = []
        for i in homeworks:
            if dt.date(*[int(j) for j in i[-1].split('.')]) > dt.datetime.now().date():
                lst.append(f'{i[0]}: {i[1]}; сделать до {i[2]}')
        bot.send_message(message.chat.id, '\n'.join(lst))
        main_window(message)
    if message.text == 'Стать админом👑':
        bot.send_message(message.chat.id, 'Введите пароль:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, admin_exam)
    if message.text == 'Добавить задание📝':
        bot.send_message(message.chat.id, 'Название предмета:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, add_homework_step_one)


@bot.message_handler(content_types='text')
def admin_exam(message):
    global ADMIN_PASSWORD
    print(message.text)
    if str(ADMIN_PASSWORD) == message.text:
        db_change_status(message)
        bot.send_message(message.chat.id, 'Статус изменён')
    else:
        bot.send_message(message.chat.id, 'Неверный код')
    main_window(message)


@bot.message_handler(content_types='text')
def add_homework_step_one(message):
    global LESSON_TITLE
    LESSON_TITLE = message.text
    bot.send_message(message.chat.id, 'Домашнее задание:')
    bot.register_next_step_handler(message, add_homework_step_two)


@bot.message_handler(content_types='text')
def add_homework_step_two(message):
    global HOMEWORK
    HOMEWORK = message.text
    bot.send_message(message.chat.id, 'Дата дедлайна(ГГГГ.ММ.ДД):')
    bot.register_next_step_handler(message, add_homework_step_three)


@bot.message_handler(content_types='text')
def add_homework_step_three(message):
    global DATE
    DATE = message.text
    db_new_homework()
    bot.send_message(message.chat.id, 'Задание добавлено')
    main_window(message)


def db_create():
    global CODE, PASSWORD, ADMIN_PASSWORD
    con = sqlite3.connect("datebase.db")
    cur = con.cursor()
    cur.execute(f'''INSERT INTO rooms(room_code, room_password,rooms_admins_password) 
                      VALUES("{CODE}", "{PASSWORD}", "{ADMIN_PASSWORD}")''').fetchall()
    con.commit()


def db():
    global CODE, PASSWORD
    con = sqlite3.connect("datebase.db")
    cur = con.cursor()
    result = cur.execute(f'''SELECT * FROM rooms 
                            WHERE room_code = "{CODE}" AND  room_password = "{PASSWORD}"''').fetchall()
    print(result)
    if result:
        return result
    else:
        return False


def db_new_homework():
    global ID, LESSON_TITLE, HOMEWORK, DATE
    con = sqlite3.connect("datebase.db")
    cur = con.cursor()
    cur.execute(f'''INSERT INTO homework(room_id, lesson, homework, date) 
                      VALUES("{ID}", "{LESSON_TITLE}", "{HOMEWORK}", "{DATE}")''').fetchall()
    con.commit()


def db_search_homework():
    con = sqlite3.connect("datebase.db")
    cur = con.cursor()
    result = cur.execute(f'''SELECT lesson, homework, date FROM homework 
                            WHERE room_id = "{ID}"''').fetchall()
    return result


def db_ne_znayu():
    con = sqlite3.connect("datebase.db")
    cur = con.cursor()
    result = cur.execute(f'''SELECT room_password FROM rooms 
                                WHERE room_code = "{CODE}"''').fetchall()
    print(result)
    if result:
        return False
    else:
        return True


def db_add_user(message):
    if func(message):
        con = sqlite3.connect("datebase.db")
        cur = con.cursor()
        cur.execute(f'''INSERT INTO users(user_id, status, first_name, last_name, username) 
                              VALUES({message.from_user.id}, "Пользователь", "{message.from_user.first_name}",
                               "{message.from_user.last_name}", "{message.from_user.username}")''').fetchall()
        con.commit()


def db_change_status(message):
    con = sqlite3.connect("datebase.db")
    cur = con.cursor()
    cur.execute(f'''UPDATE users SET status="Админ" WHERE user_id = {message.from_user.id}''').fetchall()
    con.commit()


def db_status(message):
    con = sqlite3.connect("datebase.db")
    cur = con.cursor()
    result = cur.execute(f'''SELECT status FROM users 
                                        WHERE user_id = {message.from_user.id}''').fetchall()
    return result[0][0]


def func(message):
    con = sqlite3.connect("datebase.db")
    cur = con.cursor()
    result = cur.execute(f'''SELECT * FROM users 
                                    WHERE user_id = {message.from_user.id}''').fetchall()
    if result:
        return False
    else:
        return True


if __name__ == '__main__':
    bot.infinity_polling()
