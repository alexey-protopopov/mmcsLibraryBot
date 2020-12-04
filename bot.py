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
registrationStarted = False
searchStarted = False

logging.basicConfig(level=logging.INFO, format=u'%(asctime)s - %(name)s - %(levelname)s - %(message)s')
act = Actions()


# 1)Приветствие Пользователя, выбор курса, группы, по умолчанию, семестр(Посмотреть форматирование текста tg)
@dp.message_handler(commands=['start'])
async def subscribe(message: types.Message):
    logging.info("/start command sent from user {0}".format(message.from_user.id))
    if not db.subscriber_exists(message.from_user.id):

        await message.answer(text(bold('Привет!'), bold('Спасибо, что решил воспользоваться нашим ботом!'), sep='\n'),
                             parse_mode=ParseMode.MARKDOWN_V2)
        await message.answer("Напишите номер курса и группы через точку.  (x.x)")
        act.startReg()

    else:
        # если он уже есть, то просто обновляем ему статус подписки
        # db.update_subscription(message.from_user.id, True)
        pass


@dp.message_handler(commands=['help'])
async def showHelp(message: types.Message):
    logging.info("/help command sent from user {0}".format(message.from_user.id))
    act.reset()
    await message.answer(text("Список команд:", "/files —  учебные материалы", "/search —  поиск по названию",
                              "/admin —  стать админом[TEST]",
                              "/upload — загрузка файлов", "/forget — сброс данных пользователя",
                              "/info —  информация о боте", sep='\n'))


@dp.message_handler(commands=['files'])
async def filesStore(message: types.Message):
    logging.info("/files command sent from user {0}".format(message.from_user.id))
    act.reset()
    # await message.answer('📁')
    act.startFilesMode()
    semesters_kb = act.semestersKeyboard()
    await message.answer(text(bold("Выберите семестр")), reply_markup=semesters_kb, parse_mode=ParseMode.MARKDOWN_V2)

    # user_id = message.from_user.id
    # doc = open("test.pdf", 'rb')
    # msg = await bot.send_document(user_id, doc, caption='Этот файл специально для тебя!')
    # file_id = getattr(msg, 'document').file_id
    # await message.answer(file_id)


@dp.message_handler(commands=['forget'])
async def deleteSubscriber(message: types.Message):
    logging.info("/forget command sent from user {0}".format(message.from_user.id))
    act.reset()
    if db.subscriber_exists(message.from_user.id):
        db.delete_subscriber(message.from_user.id)
        await message.answer("Данные удалены,\nиспользуйте /start для повторной регистрации.")
    else:
        await message.answer("Ошибка: пользователь не найден!")


@dp.message_handler(commands=['search'])
async def search(message: types.Message):
    logging.info("/search command sent from user {0}".format(message.from_user.id))
    act.startSearch()
    await message.answer("Что будем искать?")


@dp.message_handler()
async def actions_handler(message: types.Message):
    # Регистрация пользователя
    if not db.subscriber_exists(message.from_user.id) and act.registrationStarted:
        logging.info(
            "actions_handler()::setCourseAndGroup mode \'{0}\' command sent from user {1}"
                .format(message.text, message.from_user.id))
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
            act.stopReg()
        else:
            db.add_subscriber(message.from_user.id, 0, course, group)
            act.stopReg()
            await message.answer("Вы успешно зарегистрировались!\n Используйте /help для просмотра списка команд.")
    # Поиск по названию
    elif act.searchStarted:
        act.reset()
        logging.info("actions_handler()::search mode \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.id))
        if len(message.text) < 4:
            await message.answer("Слишком короткий запрос(минимум 4 символа).")
        else:
            dbResponse = db.search_by_name(message.text)
            results = act.generateSearchPage(dbResponse)
            await message.answer(f"Найдено результатов: {len(results)}")
            await message.answer("\n".join(results))
            act.stopSearch()
    # Отправка файла пользователю
    elif message.text.startswith("/download"):
        logging.info("actions_handler()::sendFile mode \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.id))
        try:
            user_id = message.from_user.id
            num_id = int(message.text[9:])
            file_id = db.get_file(num_id)
            await bot.send_document(user_id, file_id)
        except (ValueError, IndexError):
            await message.answer("Неверные данные! Попробуйте ещё раз.")
    # Вывод файлов/папок 0 уровень
    elif act.startFilesMode and act.filesLevel == 0 and message.text in ('1 семестр', '2 семестр'):
        disciplines_list = db.get_disciplines(message.from_user.id, int(message.text[0]))
        if disciplines_list:
            kb = act.generateDisciplinesKeyboard(disciplines_list)
            act.fLevelUp()
            await message.answer(text(bold("Выберите желаемый предмет")), reply_markup=kb, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await message.answer("<Пусто>")
        # Вывод файлов/папок 1 уровень
    elif act.startFilesMode and act.filesLevel == 1:
        disciplines_list = db.get_disciplines(message.from_user.id, int(message.text[0]))
        if disciplines_list:
            kb = act.generateDisciplinesKeyboard(disciplines_list)
            act.fLevelUp()
            await message.answer(text(bold("Выберите желаемый предмет")), reply_markup=kb,
                                 parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await message.answer("<Пусто>")

    else:
        logging.info("actions_handler():: UNKNOWN \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.id))
        await message.answer("Неизвестная команда!")


# @dp.message_handler(commands=['files'])
# async def sendFile1(message: types.Message):
# await message.answer("files")
# user_id = message.from_user.id
# msg = text(bold('Я могу ответить на следующие команды:'),
#      '/voice', '/photo', '/group', '/note', '/file, /testpre', sep='\n')
# await message.reply(msg, parse_mode=ParseMode.MARKDOWN)


# doc = open("test.pdf", 'rb')
# await bot.send_chat_action(user_id, types.ChatActions.UPLOAD_DOCUMENT)
# await asyncio.sleep(3)  # скачиваем файл и отправляем его пользователю
# msg = await bot.send_document(user_id, doc,
# caption='Этот файл специально для тебя!')
# file_id = getattr(msg, file_attr).file_id
# print(file_id)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
