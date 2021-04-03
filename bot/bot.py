import config
import logging
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import bold, code, italic, text
from aiogram.types import ParseMode

from dbManager import DbManager
from actions import Actions

bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)

db = DbManager('db.db')
logging.basicConfig(level=logging.INFO, format=u'%(asctime)s - %(name)s - %(levelname)s - %(message)s')
act = Actions()


# 1)Приветствие Пользователя, выбор курса, группы, по умолчанию, семестр(Посмотреть форматирование текста tg)
@dp.message_handler(commands=['start'])
async def subscribe(message: types.Message):
    logging.info("/start command sent from user {0}".format(message.from_user.full_name))
    if not db.subscriber_exists(message.from_user.id):

        await message.answer(text(bold('Привет!'), bold('Спасибо, что решил воспользоваться нашим ботом!'), sep='\n'),
                             parse_mode=ParseMode.MARKDOWN_V2)
        await message.answer("Напишите номер курса и группы через точку.  (x.x)")
        await message.answer("Обращаем ваше внимание, что в данный момент корректно работают только группы 2.7, 2.8, 2.9!")
        act.startReg(message.from_user.id)

    else:
        # если он уже есть, то просто обновляем ему статус подписки
        # db.update_subscription(message.from_user.id, True)
        pass


@dp.message_handler(commands=['help'])
async def showHelp(message: types.Message):
    logging.info("/help command sent from user {0}".format(message.from_user.full_name))
    act.reset(message.from_user.id)
    await message.answer(text("Список команд:", "/files —  учебные материалы", "/search —  поиск по названию",
                              "/forget — сброс данных пользователя",
                              "/info —  информация о боте", sep='\n'))


@dp.message_handler(commands=['info'])
async def showHelp(message: types.Message):
    logging.info("/info command sent from user {0}".format(message.from_user.full_name))
    act.reset(message.from_user.id)
    await message.answer(text("Бот разработан в рамках ПД 20/21", "Состав команды: ", "Протопопов Алексей, 2 курс",
                              "Щепалов Владимир, 2 курс", "Татаренко Владимир, 1 курс", "Тищенко Артëм, 1 курс",
                              "Новиков Александр,1 курс", "Обратная связь: @protopych", sep='\n'))
    await message.answer(
        "Что сейчас работает:\nНавигация по файлам(/files)\nПоиск по файлам(/search)\nСкачивание файлов\n")


@dp.message_handler(commands=['files'])
async def filesStore(message: types.Message):
    logging.info("/files command sent from user {0}".format(message.from_user.full_name))
    act.reset(message.from_user.id)
    act.startFilesMode(message.from_user.id)
    semesters_kb = act.semestersKeyboard()
    await message.answer(text(bold("Выберите семестр")), reply_markup=semesters_kb, parse_mode=ParseMode.MARKDOWN_V2)


@dp.message_handler(commands=['forget'])
async def deleteSubscriber(message: types.Message):
    logging.info("/forget command sent from user {0}".format(message.from_user.full_name))
    act.reset(message.from_user.id)
    if db.subscriber_exists(message.from_user.id):
        db.delete_subscriber(message.from_user.id)
        await message.answer("Данные удалены,\nиспользуйте /start для повторной регистрации.")
    else:
        await message.answer("Ошибка: пользователь не найден!")


@dp.message_handler(commands=['search'])
async def search(message: types.Message):
    logging.info("/search command sent from user {0}".format(message.from_user.full_name))
    act.reset(message.from_user.id)
    act.startSearch(message.from_user.id)
    await message.answer("Что будем искать?")


@dp.callback_query_handler(lambda c: c.data == 'right')
async def process_callback_button_right(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    act.statements[callback_query.from_user.id]["search_pages_position"] += 1
    pos = act.statements[callback_query.from_user.id]["search_pages_position"]
    pages = "\n".join(act.statements[callback_query.from_user.id]["search_pages"][(pos - 1)*4:(pos-1)*4+4])
    pages += "\n Страница {0}/{1}".format(pos, act.statements[callback_query.from_user.id]["search_pages_count"])
    if pos == act.statements[callback_query.from_user.id]["search_pages_count"]:
        kb = act.searchKeyboardEnd()
    else:
        kb = act.searchKeyboardMid()
    await bot.send_message(callback_query.from_user.id, pages, reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data == 'left')
async def process_callback_button_left(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    act.statements[callback_query.from_user.id]["search_pages_position"] -= 1
    pos = act.statements[callback_query.from_user.id]["search_pages_position"]
    pages = "\n".join(act.statements[callback_query.from_user.id]["search_pages"][(pos - 1)*4:(pos-1)*4+4])
    pages += "\n Страница {0}/{1}".format(pos, act.statements[callback_query.from_user.id]["search_pages_count"])
    if pos == 1:
        kb = act.searchKeyboardBegin()
    else:
        kb = act.searchKeyboardMid()
    await bot.send_message(callback_query.from_user.id, pages, reply_markup=kb)


@dp.message_handler()
async def actions_handler(message: types.Message):
    # Регистрация пользователя
    if not db.subscriber_exists(message.from_user.id) and act.registrationStarted(message.from_user.id):
        logging.info("actions_handler()::setCourseAndGroup mode \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.full_name))
        userInput = message.text.split('.')
        print(userInput)
        try:
            course = int(userInput[0])
            group = int(userInput[1])
        except (ValueError, IndexError):
            course = -1
            group = -1
        if course not in range(1, 5) or (group not in range(1, 15) and (group != 45 and group != 57)):
            await message.answer("Неверные данные! Попробуйте ещё раз:\n/start")
            act.stopReg(message.from_user.id)
        else:
            db.add_subscriber(message.from_user.id, 0, course, group)
            act.stopReg(message.from_user.id)
            await message.answer("Вы успешно зарегистрировались!\n Используйте /help для просмотра списка команд.")
    # Поиск по названию
    elif act.searchStarted(message.from_user.id):
        # act.reset(message.from_user.id)
        logging.info("actions_handler()::search mode \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.full_name))
        if not len(message.text):
            await message.answer("Задан пустой запрос.")
        else:
            dbResponse = db.search_by_name(message.text)
            results = act.generateSearchPage(dbResponse, message.from_user.id)
            print(results)
            if results:
                await message.answer(f"Найдено результатов: {len(results)}")
            results = "\n".join(results[0:4])
            results += "\n Страница {0}/{1}".format(act.search_pages_position(message.from_user.id), act.search_pages_count(message.from_user.id))
            if act.search_pages_count(message.from_user.id) == 0:
                await message.answer("Ничего не найдено!")
            else:
                if act.search_pages_count(message.from_user.id) == 1:
                    kb = types.InlineKeyboardMarkup()
                else:
                    kb = act.searchKeyboardBegin()

                msg = await message.answer(results, reply_markup=kb)
                act.stopSearch(message.from_user.id)
    # Отправка файла пользователю
    elif message.text.startswith("/download"):
        logging.info("actions_handler()::sendFile mode \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.full_name))
        try:
            user_id = message.from_user.id
            num_id = int(message.text[9:])
            file_id = db.get_file(num_id)
            await bot.send_document(user_id, file_id)
        except (ValueError, IndexError):
            await message.answer("Неверные данные! Попробуйте ещё раз.")
    # Вывод файлов/папок 0 уровень
    elif act.filesLevel(message.from_user.id) == 1 and message.text == '⤴️На уровень выше':
        act.reset(message.from_user.id)
        act.startFilesMode(message.from_user.id)
        semesters_kb = act.semestersKeyboard()
        await message.answer(text(bold("Выберите семестр")), reply_markup=semesters_kb,
                             parse_mode=ParseMode.MARKDOWN_V2)

    elif act.isFilesMode(message.from_user.id) and (act.filesLevel(message.from_user.id) == 0 and message.text in ('1 семестр', '2 семестр',) or (
            message.text == '⤴️На уровень выше' and act.filesLevel == 2)):

        logging.info("actions_handler()::FilesStore mode(level0) \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.full_name))
        if message.text == '⤴️На уровень выше':
            act.statements[message.from_user.id]["filesLevel"] = 0
            act.statements[message.from_user.id]["currentDiscipline"] = ""
            act.statements[message.from_user.id]["currentFolder"] = ""
        if act.semester(message.from_user.id) == 0:
            act.statements[message.from_user.id]["semester"] = int(message.text[0])
        disciplines_list = db.get_disciplines(message.from_user.id, act.semester(message.from_user.id))
        if disciplines_list:
            kb = act.generateDisciplinesKeyboard(disciplines_list)
            act.fLevelUp(message.from_user.id)
            await message.answer(text(bold("Выберите желаемый предмет")), reply_markup=kb,
                                 parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await message.answer("<Пусто>")
    # Вывод файлов/папок 1 уровень
    elif act.isFilesMode(message.from_user.id) and (act.filesLevel(message.from_user.id) == 1 or (act.filesLevel(message.from_user.id) == 3 and message.text == '⤴️На уровень выше')):
        logging.info("actions_handler()::FilesStore mode(level1) \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.full_name))
        if message.text == '⤴️На уровень выше':
            act.fLevelDown(message.from_user.id)
            act.fLevelDown(message.from_user.id)
            act.statements[message.from_user.id]["currentFolder"] = ""
        if message.text != '⤴️На уровень выше':
            act.statements[message.from_user.id]["currentDiscipline"] = message.text
        folders_list = db.get_folders_by_discipline(message.from_user.id, act.semester(message.from_user.id), act.currentDiscipline(message.from_user.id))
        if folders_list:
            kb = act.generateFoldersKeyboard(folders_list)
            await message.answer(text(bold("Выберите желаемый раздел")), reply_markup=kb,
                                 parse_mode=ParseMode.MARKDOWN_V2)
            act.fLevelUp(message.from_user.id)

        else:
            await message.answer("<Пусто>")
    # Вывод файлов/папок 2 уровень
    elif act.isFilesMode(message.from_user.id) and (
            (act.filesLevel(message.from_user.id) == 2 and message.text != '⤴️На уровень выше') or (
            act.filesLevel(message.from_user.id) == 4 and message.text == '⤴️На уровень выше')):
        logging.info("actions_handler()::FilesStore2 mode(level{0}) \'{1}\' command sent from user {2}"
                     .format(act.filesLevel(message.from_user.id)
                             , message.text, message.from_user.full_name))
        if message.text == '⤴️На уровень выше':
            act.fLevelDown(message.from_user.id)
            act.fLevelDown(message.from_user.id)
        if not act.currentFolder(message.from_user.id):
            act.statements[message.from_user.id]["currentFolder"] = message.text[2:]

        files_list = db.get_files_from_folder(message.from_user.id, act.semester(message.from_user.id), act.currentDiscipline(message.from_user.id),
                                              act.currentFolder(message.from_user.id))
        if files_list:
            kb = act.generateFilesKeyboard(files_list)
            await message.answer(text(bold("Выберите желаемый раздел")), reply_markup=kb,
                                 parse_mode=ParseMode.MARKDOWN_V2)
            act.fLevelUp(message.from_user.id)
        else:
            await message.answer("<Пусто>")
    # Вывод файлов/папок 3 уровень
    elif act.isFilesMode(message.from_user.id) and (act.filesLevel(message.from_user.id) == 3 and message.text != '⤴️На уровень выше'):
        logging.info("actions_handler()::FilesStore mode(level3) \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.full_name))
        file_record = db.get_file_record(message.from_user.id, act.semester(message.from_user.id), act.currentDiscipline(message.from_user.id), act.currentFolder(message.from_user.id),
                                         message.text[2:])

        if file_record:
            file_page = act.generateFilePage(file_record)
            kb = act.FolderLevelUpKeyboard()
            await message.answer(file_page, reply_markup=kb)
            act.fLevelUp(message.from_user.id)
        else:
            await message.answer("<Пусто>")
    else:
        logging.info("actions_handler():: UNKNOWN \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.full_name))
        await message.answer("Неизвестная команда!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
