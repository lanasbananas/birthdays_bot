from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import executor
import datetime
import asyncio
import states_errors
import database


bot = Bot('TOKEN')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


def main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button_add = KeyboardButton("Добавить День Рождения⏬")
    button_see = KeyboardButton("Посмотреть Дни Рождения👀")
    button_delete = KeyboardButton("Удалить День Рождения❌")
    button_time = KeyboardButton("Поменять время напоминания⏰")
    buttons = [
        [button_add],
        [button_see],
        [button_delete],
        [button_time]
    ]
    keyboard.keyboard = buttons
    return keyboard


def cancel_button():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button = KeyboardButton('Отмена')
    keyboard.add(button)
    return keyboard


async def check_birthdays():
    while True:
        date = await database.get_dates()
        name = await database.get_names()
        useridies = await database.get_userid()
        date1 = []
        date2 = []
        for k in range(len(date)):
            time_ = (await database.get_time_on_userid(useridies[k]))[0]
            h = time_.hour
            m = time_.minute
            date1.append(datetime.datetime(date[k].year, date[k].month, date[k].day) - datetime.timedelta(
                days=1) + datetime.timedelta(hours=h, minutes=m))
            date2.append(datetime.datetime(date[k].year, date[k].month, date[k].day) - datetime.timedelta(
                weeks=1) + datetime.timedelta(hours=h, minutes=m))
        for i in range(len(date)):
            if date1[i].strftime("%m-%d %H:%M") == (datetime.datetime.today() + datetime.timedelta(hours=1)).strftime("%m-%d %H:%M"):
                old = datetime.datetime.today().year - date1[i].year
                y = int(old)
                await send_reminder(useridies[i], name[i], y, 0)
            if date2[i].strftime("%m-%d %H:%M") == (datetime.datetime.today() + datetime.timedelta(hours=1)).strftime("%m-%d %H:%M"):
                old = datetime.datetime.today().year - date2[i].year
                y = int(old)
                await send_reminder(useridies[i], name[i], y, 1)
            if (i==(len(date)-1)):
                await asyncio.sleep(60)



async def send_reminder(chat_id, friend_name, year, fl):
    if (fl==0):
        message = f"Завтра день рождения у {friend_name}! Не забудьте поздравить с {year}-летим🙂"
    else:
        message = f"Через неделю {friend_name} празднует {year}-летие! Вы еще успеете подготовить подарок😉🎁" \
                  f"\n\nЗа день до дня рождения я отправлю еще одно напоминание, чтобы вы не забыли поздравить🙂"
    await bot.send_message(chat_id, message)


@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    await message.answer(f'Привет, {user_name}! Я бот-напоминалка о Днях Рождения друзей!🎁\nСкорее воспользуйся моим функционалом!👇🏻', reply_markup=main_menu())
    if len(await database.get_id_on_userid(user_id)) == 0:
        await database.add_user(user_id)


@dp.message_handler(lambda message: message.text == 'Посмотреть Дни Рождения👀')
async def handle_see_birthday(message: types.Message):
    user_id = message.from_user.id
    dates = await database.get_dates_on_userid(user_id)
    names = await database.get_names_on_userid(user_id)
    if len(names) == 0:
        await message.answer('Список пуст', reply_markup=main_menu())
    else:
        # Создаем список кортежей (месяц, день, имя) для сортировки по месяцам и дням
        birthday_data = [(date.month, date.day, name) for date, name in zip(dates, names)]
        # Сортируем список по месяцам и дням
        sorted_birthday_data = sorted(birthday_data, key=lambda x: (x[0], x[1]))
        mes = ''
        for month, day, name in sorted_birthday_data:
            mes = f'{mes}{day:02d}.{month:02d} - {name}\n'
        await message.answer(mes)


@dp.message_handler(lambda message: message.text == 'Добавить День Рождения⏬')
async def handle_add_birthday(message: types.Message):
    await message.answer("Введите имя друга:", reply_markup=cancel_button())
    await states_errors.AddBirthdayState.Name.set()


@dp.message_handler(state=states_errors.AddBirthdayState.Name)
async def ask_birthday(message: types.Message, state: FSMContext):
    friend_name = message.text
    try:
        if friend_name == 'Отмена':
            raise states_errors.Cancel('cancel')
        await state.update_data(friend_name=friend_name)
        await message.answer("Введите его дату рождения:", reply_markup=cancel_button())
        await states_errors.AddBirthdayState.Date.set()
    except states_errors.Cancel:
        await message.answer("Действие отменено", reply_markup=main_menu())
        await state.finish()


@dp.message_handler(state=states_errors.AddBirthdayState.Date)
async def save_birthday(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    friend_name = data.get('friend_name')
    try:
        if message.text == 'Отмена':
            raise states_errors.Cancel('cancel')
        birthday = datetime.datetime.strptime(message.text, "%d.%m.%Y")
        await database.add_birthday(user_id, birthday.date(), friend_name)
        await message.answer(f"День рождения для {friend_name} успешно добавлен!", reply_markup=main_menu())
        await state.finish()
    except ValueError:
        await message.answer("Некорректный формат даты. Введите дату рождения в формате дд.мм.гггг снова:")
        await states_errors.AddBirthdayState.Date.set()
        await state.update_data(friend_name=friend_name)
    except states_errors.Cancel:
        await message.answer("Действие отменено", reply_markup=main_menu())
        await state.finish()


@dp.message_handler(lambda message: message.text == 'Удалить День Рождения❌')
async def handle_delete_birthday(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    dates = await database.get_dates_on_userid(user_id)
    names = await database.get_names_on_userid(user_id)
    if len(names) == 0:
        await message.answer('Список пуст', reply_markup=main_menu())
    else:
        # Создаем список кортежей (месяц, день, имя) для сортировки по месяцам и дням
        birthday_data = [(date.month, date.day, name) for date, name in zip(dates, names)]
        # Сортируем список по месяцам и дням
        sorted_birthday_data = sorted(birthday_data, key=lambda x: (x[0], x[1]))
        mes = 'Выберите номер строки, которую хотите удалить: \n\n'
        i = 1
        for month, day, name in sorted_birthday_data:
            mes = f'{mes}{i}. {day:02d}.{month:02d} - {name}\n'
            i += 1
        await message.answer(mes, reply_markup=cancel_button())
        await states_errors.DeleteBirthdayState.Numbers.set()


@dp.message_handler(state=states_errors.DeleteBirthdayState.Numbers)
async def ask_del_birthday(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    idies = await database.get_birthday_on_userid_sorted(user_id)
    try:
        if message.text == 'Отмена':
            raise states_errors.Cancel('cancel')
        num = int(message.text)
        if num > len(idies) or num < 1:
            raise ValueError('nonum')
        await database.delete_birthday(idies[num-1])
        await message.answer("Строка успешно удалена!", reply_markup=main_menu())
        await state.finish()
    except ValueError:
        await message.answer("Такого номера нет в списке. Введите число снова:", reply_markup=cancel_button())
        await states_errors.DeleteBirthdayState.Numbers.set()
    except states_errors.Cancel:
        await message.answer("Действие отменено", reply_markup=main_menu())
        await state.finish()


@dp.message_handler(lambda message: message.text == 'Поменять время напоминания⏰')
async def handle_time(message: types.Message):
    await message.answer("Введите время оповещения:", reply_markup=cancel_button())
    await states_errors.AddTimeState.Data.set()


@dp.message_handler(state=states_errors.AddTimeState.Data)
async def ask_time(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        if message.text == 'Отмена':
            raise states_errors.Cancel('cancel')
        _time = message.text
        _time = datetime.datetime.strptime(_time, "%H:%M")
        await database.update_time(user_id, _time)
        await message.answer("Время успешно добавлено!", reply_markup=main_menu())
        await state.finish()
    except ValueError:
        await message.answer("Некорректный формат времени. Введите время в формате чч:мм снова:", reply_markup=cancel_button())
        await states_errors.AddTimeState.Data.set()
    except states_errors.Cancel:
        await message.answer("Действие отменено", reply_markup=main_menu())
        await state.finish()


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(f"Я не знаю, что ответить на это😕 Если хотите воспользоваться моим функционалом, нажмите на кнопки ниже👇🏻")




    # Запуск бота
    await executor.start_polling(dp, skip_updates=True)
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(database.create_database())

    # Создаем и запускаем задачу для фоновой проверки
    loop.create_task(check_birthdays())

    executor.start_polling(dp, skip_updates=True)
