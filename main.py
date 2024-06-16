import telebot
from telebot import types
import os
import shutil
from data_base.schema import Preferences
from crop_letters import find_letters
from text_handling import letters_to_files
from background import Background
from background_types.squared_back import SQUARED_BACK
from crop_letters import overlay_transparent

import cv2

bot = telebot.TeleBot("6231089734:AAG3ZPycOex1pSSfkfuY0qQ3kC1iYxZ3JJI")


@bot.message_handler(commands=['start', 'help'])
def start(message: types.Message):  # все команды
    Preferences.get_or_create(user_id=message.from_user.id)
    help_message = """ 
/start или /help - все команды бота
/update_handwriting - обновляет почерк пользователя
/get_handwriting - выдает последний сохраненный почерк пользователя
/update_background - выбор фона
/update_name - обновляет подпись
/get_name - выдает подпись пользователя
/update_font - обновляет размер шрифта
/update_kerning - обновляет межбуквенное расстояние
    """
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}! {help_message}')


@bot.message_handler(commands=['get_handwriting'])
def get_handwriting(picture):  # выдает последний почерк пользователя
    path = os.path.join('pictures', f'{picture.from_user.id}.jpg')
    if not os.path.exists(path):
        bot.send_message(picture.chat.id, "У Вас еще нет почерка. Добавьте его, отправив фото")
    with open(path, 'rb') as f:
        photo = f.read()
    bot.send_photo(picture.chat.id, photo)


@bot.message_handler(commands=['update_handwriting'])
def next_handler_handwriting_1(picture: types.Message):
    bot.reply_to(picture, "Заглавные буквы обновлены")

    # добавление заглавных букв


@bot.message_handler(commands=['update_handwriting'])
def update_handwriting(message: types.Message):  # обновление почерка
    msg = bot.send_message(message.chat.id, """
    Отправьте фотографию заглавных букв в одну строчку.
    Старайтесь, чтобы буквы были видны и не накладывались друг на друга.
    На фотографии не должно быть ничего, кроме букв и фона белого листа 
    (желательно использовать лист А4)
    """)
    bot.register_next_step_handler(msg, next_handler_handwriting_1)


@bot.message_handler(content_types=['photo'])
def update_handwriting(picture: types.Message):  # опрос про обновление почерка
    file_id = picture.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    path = os.path.join('last_pictures', f'{picture.from_user.id}.jpg')
    with open(path, 'wb') as f:
        f.write(downloaded_file)
    button_yes = types.InlineKeyboardButton("Да", callback_data="yes.update.photo")
    button_no = types.InlineKeyboardButton("Нет", callback_data="no.update.photo")
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(button_yes)
    keyboard.add(button_no)
    bot.reply_to(picture, "Вы уверены, что хотите обновить почерк?", reply_markup=keyboard)
    # чел нажал кнопку и callback_data вернулась на родину
    # bot.send_photo(picture.chat.id, picture.photo[-1].file_id, picture.caption)


@bot.callback_query_handler(func=lambda call: call.data in ["yes.update.photo", "no.update.photo"])
def add_handwriting(answer: types.CallbackQuery):  # обработка опроса про обновление почерка
    if answer.data == "yes.update.photo":
        last_photo_path = os.path.join('last_pictures', f'{answer.from_user.id}.jpg')
        path = os.path.join('pictures', f'{answer.from_user.id}.jpg')
        shutil.copy(last_photo_path, path)
        find_letters(answer.from_user.id)
        bot.edit_message_text("Ваш почерк успешно обновлен!", answer.from_user.id, answer.message.id)
    else:
        bot.edit_message_text("Фото проигнорировано", answer.from_user.id, answer.message.id)
    # bot.edit_message_reply_markup(answer.from_user.id, answer.message.id, reply_markup=None)


@bot.message_handler(commands=['update_background'])
def update_background(message: types.Message):  # опрос про обновление фона
    line = types.InlineKeyboardButton("Тетрадь в клетку", callback_data="b0")
    checker = types.InlineKeyboardButton("Тетрадь в линейку", callback_data="b1")
    paper = types.InlineKeyboardButton("Лист А4", callback_data="b2")
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(line)
    keyboard.add(checker)
    keyboard.add(paper)
    bot.reply_to(message, "Выберите фон:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ["b0", "b1", "b2"])
def add_background(message: types.CallbackQuery):  # обработка опроса про обновление фона
    bot.edit_message_text("Ваш фон успешно обновлен", message.from_user.id, message.message.id)
    if message.data == "b0":
        answer = 0
    elif message.data == "b1":
        answer = 1
    else:
        answer = 2
    query = Preferences.update(background=answer).where(Preferences.user_id == message.from_user.id)
    query.execute()
    # добавление фона в базу данных


def next_handler_name(message: types.Message):
    bot.reply_to(message, "Ваша подпись обновлена")
    query = Preferences.update(name=message.text).where(Preferences.user_id == message.from_user.id)
    query.execute()
    # добавление подписи в базу данных


@bot.message_handler(commands=['update_name'])
def update_name(message: types.Message):  # обновление подписи
    msg = bot.send_message(message.chat.id, "Введите новую подпись")
    bot.register_next_step_handler(msg, next_handler_name)


@bot.message_handler(commands=['get_name'])
def get_name(message: types.Message):  # обновление подписи
    query = Preferences.select().where(Preferences.user_id == message.from_user.id)
    if not query.exists():
        return
    row = query.get()
    if row.name is not None:
        bot.send_message(message.from_user.id, f"Ваша подпись: {row.name}")
        return
    bot.send_message(message.from_user.id, "У вас еще нет подписи. Добавить ее можно с помощью /update_name")


def next_handler_font(message: types.Message):
    bot.reply_to(message, "Размер шрифта обновлен")
    query = Preferences.update(font_size=message.text).where(Preferences.user_id == message.from_user.id)
    query.execute()
    # добавление размер шрифта в базу данных


@bot.message_handler(commands=['update_font'])
def update_name(message: types.Message):  # обновление размера шрифта
    msg = bot.send_message(message.chat.id, "Введите число от 1 до 10")
    bot.register_next_step_handler(msg, next_handler_font)


def next_handler_kerning(message: types.Message):
    bot.reply_to(message, "Кернинг обновлен")
    query = Preferences.update(kerning=message.text).where(Preferences.user_id == message.from_user.id)
    query.execute()
    # добавление кернинга в базу данных


@bot.message_handler(commands=['update_kerning'])
def update_name(message: types.Message):  # обновление кернинга
    msg = bot.send_message(message.chat.id, "Введите число от 1 до 10")
    bot.register_next_step_handler(msg, next_handler_kerning)


@bot.message_handler(content_types=['text'])
def result_photo(message: types.Message):
    words = letters_to_files(message.text)

    background = Background(**SQUARED_BACK, user_id=message.from_user.id)
    background_jpg = cv2.imread('square_background.jpg')
    for word in words:
        for i, (x, y) in enumerate(background.apply(word)):
            path2letter = os.path.join('letters', f'{message.from_user.id}', f'{word[i]}.png')
            letter = cv2.imread(path2letter, -1)
            letter_height = letter.shape[0]

            # пытаемся как-то поровнее размещать буквы, потому что не все из них умещаются в клеточку
            if word[i] in {'4', '8', '17', '20', '21', '23', '26'}: # "большие буквы c хвостиком вниз": д, з и т.д
                letter_height //= 2
            if letter_height < background.vert_space // 2:
                y += (background.vert_space // 2 - letter_height)
            else:
                y -= (letter_height - background.vert_space // 2)
            # в целом if'ы выше можно повыкидывать спокойно и все должно работать

            # вызываем метод для того, чтобы наложить букву без фона на фон, (x, y) - позиция левого верхнего угла буквы
            # на фоне
            background_jpg = overlay_transparent(background_jpg, letter, x, y)

    cv2.imwrite("tmp.jpg", background_jpg)
    with open("tmp.jpg", 'rb') as f:
        photo = f.read()

    bot.send_photo(message.chat.id, photo)


bot.infinity_polling()
