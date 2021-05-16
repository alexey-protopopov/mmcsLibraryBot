import config
import logging
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import bold, code, italic, text
from aiogram.types import ParseMode
from os import remove as f_remove

from dbManager import DbManager, check_course_group
from actions import Actions

bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)

db = DbManager('db.db')
logging.basicConfig(level=logging.INFO, format=u'%(asctime)s - %(name)s - %(levelname)s - %(message)s')
act = Actions()

AGENT_ID = 1738887702


# 1)Приветствие Пользователя, выбор курса, группы, по умолчанию, семестр(Посмотреть форматирование текста tg)
@dp.message_handler(commands=['start'])
async def subscribe(message: types.Message):
    logging.info("/start command sent from user {0}".format(message.from_user.full_name))
    if not db.subscriber_exists(message.from_user.id):
        report = f"New user: {message.from_user.full_name}({message.from_user.id})"
        await bot.send_message(AGENT_ID, report)
        await message.answer(text(bold('Привет!'), bold('Спасибо, что решил воспользоваться нашим ботом!'), sep='\n'),
                             parse_mode=ParseMode.MARKDOWN_V2)
        await message.answer("Напишите номер курса и группы через точку.  (x.x)")
        await message.answer(
            "Обращаем ваше внимание, что в данный момент корректно работают только группы 2.7, 2.8, 2.9!")
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
                              "/forget — сброс данных пользователя", "/admin — получить права админа[TEST]",
                              "/upload — загрузить файл", "/delete — удалить файл", "/mkdir — создать папку",
                              "/rmdir — удалить папку", "/status —  информация о пользователе",
                              "/info —  информация о боте", sep='\n'))


@dp.message_handler(commands=['info'])
async def showHelp(message: types.Message):
    logging.info("/info command sent from user {0}".format(message.from_user.full_name))
    act.reset(message.from_user.id)
    await message.answer(text("Бот разработан в рамках ПД 20/21", "Состав команды: ", "Протопопов Алексей, 2 курс",
                              "Щепалов Владимир, 2 курс", "Татаренко Владимир, 1 курс", "Тищенко Артëм, 1 курс",
                              "Новиков Александр,1 курс", "Обратная связь: @protopych", sep='\n'))
    await message.answer(
        "Что сейчас работает:\nНавигация по файлам(/files)\nПоиск по файлам(/search)\nСкачивание файлов\nЗагрузка/удаление файлов\nСоздание/удаление папок")


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
    pages = "\n".join(act.statements[callback_query.from_user.id]["search_pages"][(pos - 1) * 4:(pos - 1) * 4 + 4])
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
    pages = "\n".join(act.statements[callback_query.from_user.id]["search_pages"][(pos - 1) * 4:(pos - 1) * 4 + 4])
    pages += "\n Страница {0}/{1}".format(pos, act.statements[callback_query.from_user.id]["search_pages_count"])
    if pos == 1:
        kb = act.searchKeyboardBegin()
    else:
        kb = act.searchKeyboardMid()
    await bot.send_message(callback_query.from_user.id, pages, reply_markup=kb)


# скачивает файл и добавляет его в бд
@dp.message_handler(content_types=['document'])
async def upload_doc(message: types.Message):
    logging.info(
        "/upload_doc command sent from user {0}({1})".format(message.from_user.full_name, message.from_user.id))

    if act.isUploadMode(message.from_user.id) and (act.semester(message.from_user.id) != 0) and (
            act.currentDiscipline(message.from_user.id) != "") and (
            act.currentFolder(message.from_user.id)) != "":
        document_id = message.document.file_id
        name = message.document.file_name
        if db.file_exists(name, act.currentDiscipline(message.from_user.id), act.currentFolder(message.from_user.id)):
            await message.answer("Такой файл уже существует!")
            act.reset(message.from_user.id)
            return
        try:
            file_info = await bot.get_file(document_id)
        except Exception as e:
            await message.answer("Ошибка при загрузке!(size > 20 мб?)")
            print(e)
            act.reset(message.from_user.id)
            return

        fi = file_info.file_path
        await bot.download_file(fi, name)
        with open(name, 'rb') as file:
            try:
                msg = await bot.send_document(AGENT_ID, file, disable_notification=True)
                file_id = getattr(msg, 'document').file_id
                db.add_file(file_id, name, db.get_user_info(message.from_user.id)[3],
                            db.get_user_info(message.from_user.id)[5],
                            act.semester(message.from_user.id), act.currentDiscipline(message.from_user.id),
                            act.currentFolder(message.from_user.id), message.from_user.id)
                report = f'Successfully uploaded by {message.from_user.full_name}({message.from_user.id})\nand saved to DB file "{name}"'
                logging.info(report)
                await bot.send_message(AGENT_ID, report)
                act.reset(message.from_user.id)
                await message.answer("Загрузка успешно завершена!")

            except Exception as e:
                logging.error('Couldn\'t upload {}. Error is {}'.format(name, e))
                act.reset(message.from_user.id)
                return
        f_remove(name)  # удаляем файл с устройства после завершения работы
    else:
        await message.answer("Не соблюдены все условия!")


@dp.message_handler(commands=['upload'])
async def upload(message: types.Message):
    logging.info("/upload command sent from user {0}({1})".format(message.from_user.full_name, message.from_user.id))
    act.reset(message.from_user.id)
    if db.get_user_info(message.from_user.id)[2] == 1:
        await message.answer("[Режим загрузки]")
        act.startUpload(message.from_user.id)
        semesters_kb = act.semestersKeyboard()
        await message.answer(text(bold("Выберите семестр")), reply_markup=semesters_kb,
                             parse_mode=ParseMode.MARKDOWN_V2)

    else:
        await message.answer("Недостаточно прав, используйте /admin, чтобы получить права на загрузку")


@dp.message_handler(commands=['mkdir'])
async def mkdir(message: types.Message):
    logging.info("/mkdir command sent from user {0}({1})".format(message.from_user.full_name, message.from_user.id))
    act.reset(message.from_user.id)
    if db.get_user_info(message.from_user.id)[2] == 1:
        await message.answer("[Создание новой папки]")
        act.startMkdir(message.from_user.id)
        semesters_kb = act.semestersKeyboard()
        await message.answer(text(bold("Выберите семестр")), reply_markup=semesters_kb,
                             parse_mode=ParseMode.MARKDOWN_V2)

    else:
        await message.answer("Недостаточно прав, используйте /admin, чтобы получить права")


@dp.message_handler(commands=['rmdir'])
async def rmdir(message: types.Message):
    logging.info("/rmdir command sent from user {0}({1})".format(message.from_user.full_name, message.from_user.id))
    act.reset(message.from_user.id)
    if db.get_user_info(message.from_user.id)[2] == 1:
        await message.answer("[Удаление папки]")
        act.startRmdir(message.from_user.id)
        semesters_kb = act.semestersKeyboard()
        await message.answer(text(bold("Выберите семестр")), reply_markup=semesters_kb,
                             parse_mode=ParseMode.MARKDOWN_V2)

    else:
        await message.answer("Недостаточно прав, используйте /admin, чтобы получить права")


@dp.message_handler(commands=['delete'])
async def delete(message: types.Message):
    logging.info("/delete command sent from user {0}({1})".format(message.from_user.full_name, message.from_user.id))
    act.reset(message.from_user.id)
    if db.get_user_info(message.from_user.id)[2] == 1:
        await message.answer("[Режим удаления]")
        act.startDelete(message.from_user.id)
        semesters_kb = act.semestersKeyboard()
        await message.answer(text(bold("Выберите семестр: ")), reply_markup=semesters_kb,
                             parse_mode=ParseMode.MARKDOWN_V2)

    else:
        await message.answer("Недостаточно прав, используйте /admin, чтобы получить права на удаление")


@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    logging.info("/admin command sent from user {0}({1})".format(message.from_user.full_name, message.from_user.id))
    act.reset(message.from_user.id)
    db.set_admin(message.from_user.id)
    await message.answer("Вы стали админом!")


@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    logging.info("/status command sent from user {0}({1})".format(message.from_user.full_name, message.from_user.id))
    act.reset(message.from_user.id)
    if db.subscriber_exists(message.from_user.id):
        uinfo = db.get_user_info(message.from_user.id)
        user_status = ("Пользователь", "Админ")
        print(uinfo)
        ans = f"Имя: {message.from_user.full_name}\nКурс: {uinfo[3]}\nГруппа: {uinfo[4]}\nНаправление: {uinfo[5]}\n" \
              f"Уровень доступа: {user_status[uinfo[2]]}"
        await message.answer(ans)
    else:
        await message.answer("Вы не зарегистрированы!")


@dp.message_handler()
async def actions_handler(message: types.Message):
    # Регистрация пользователя
    if not db.subscriber_exists(message.from_user.id) and act.registrationStarted(message.from_user.id):
        logging.info("actions_handler()::setCourseAndGroup mode \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.full_name))
        userInput = message.text.split('.')
        try:
            course = int(userInput[0])
            group = int(userInput[1])
        except (ValueError, IndexError):
            course = -1
            group = -1
        if not check_course_group(course, group):
            await message.answer("Неверные данные! Попробуйте ещё раз:\n/start")
            act.stopReg(message.from_user.id)
        else:
            db.add_subscriber(message.from_user.id, 0, course, group)
            act.stopReg(message.from_user.id)
            await message.answer("Вы успешно зарегистрировались!\n Используйте /help для просмотра списка команд.")

    # Поиск по названию
    elif act.searchStarted(message.from_user.id):
        logging.info("actions_handler()::search mode \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.full_name))
        if not len(message.text):
            await message.answer("Задан пустой запрос.")
        else:
            dbResponse = db.search_by_name(message.text)
            results = act.generateSearchPage(dbResponse, message.from_user.id)
            # print(results)
            if results:
                await message.answer(f"Найдено результатов: {len(results)}")
            results = "\n".join(results[0:4])
            results += "\n Страница {0}/{1}".format(act.search_pages_position(message.from_user.id),
                                                    act.search_pages_count(message.from_user.id))
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

    # /files
    elif act.isFilesMode(message.from_user.id):

        # print(act.statements[message.from_user.id])

        # Вывод файлов/папок 0 уровень[выбор семестра]
        if act.filesLevel(message.from_user.id) == 0 or ((act.filesLevel(message.from_user.id) == 1 or act.filesLevel(
                message.from_user.id) == 2) and message.text == '⤴️На уровень выше'):
            logging.info("actions_handler()::FilesStore mode(level0) \'{0}\' command sent from user {1}({2})"
                         .format(message.text, message.from_user.full_name, message.from_user.id))
            # print("l0 start ", act.statements[message.from_user.id])

            act.reset(message.from_user.id)
            act.startFilesMode(message.from_user.id)
            semesters_kb = act.semestersKeyboard()
            await message.answer(text(bold("Выберите семестр:")), reply_markup=semesters_kb,
                                 parse_mode=ParseMode.MARKDOWN_V2)

        #  print("l0 end ", act.statements[message.from_user.id])
        # Вывод файлов/папок 1 уровень[вывод доступных предметов в семестре]
        elif act.filesLevel(message.from_user.id) == 1 or (
                act.filesLevel(message.from_user.id) == 3 and message.text == '⤴️На уровень выше'):
            logging.info("actions_handler()::FilesStore mode(level1) \'{0}\' command sent from user {1}({2})"
                         .format(message.text, message.from_user.full_name, message.from_user.id))
            if message.text == '⤴️На уровень выше':
                act.statements[message.from_user.id]["filesLevel"] = 1
                act.statements[message.from_user.id]["currentDiscipline"] = ""
            if act.semester(message.from_user.id) == 0:
                try:
                    act.statements[message.from_user.id]["semester"] = int(message.text[0])
                except ValueError:
                    act.reset(message.from_user.id)
                    await message.answer("Неверные данные!")
            disciplines_list = db.get_disciplines(message.from_user.id, act.semester(message.from_user.id))
            # print("l1 ", act.statements[message.from_user.id])
            if disciplines_list:
                kb = act.generateDisciplinesKeyboard(disciplines_list)

                act.fLevelUp(message.from_user.id)
                await message.answer(text(bold("Выберите желаемый предмет:")), reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN_V2)

            else:
                act.reset(message.from_user.id)
                await message.answer("<Пусто>")

        # Вывод файлов/папок 2 уровень[вывод доступных подразделов для выбранного предмета]
        elif act.filesLevel(message.from_user.id) == 2 or (
                act.filesLevel(message.from_user.id) == 4 and message.text == '⤴️На уровень выше'):
            logging.info("actions_handler()::FilesStore mode(level2) \'{0}\' command sent from user {1}({2})"
                         .format(message.text, message.from_user.full_name, message.from_user.id))
            if message.text == '⤴️На уровень выше':
                act.statements[message.from_user.id]["filesLevel"] = 2
                act.statements[message.from_user.id]["currentFolder"] = ""

            if not act.currentDiscipline(message.from_user.id) and message.text != '⤴️На уровень выше':
                act.statements[message.from_user.id]["currentDiscipline"] = message.text
            folders_list = db.get_folders_by_discipline(message.from_user.id, act.semester(message.from_user.id),
                                                        act.currentDiscipline(message.from_user.id))
            # print("l2 ", act.statements[message.from_user.id])
            if folders_list:
                kb = act.generateFoldersKeyboard(folders_list)
                act.fLevelUp(message.from_user.id)
                await message.answer(text(bold("Выберите желаемый раздел:")), reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN_V2)
            else:
                act.reset(message.from_user.id)
                await message.answer("<Пусто>")

        # Вывод файлов/папок 3 уровень[вывод файлов из папки]
        elif act.filesLevel(message.from_user.id) == 3 or (
                act.filesLevel(message.from_user.id) == 5 and message.text == '⤴️На уровень выше'):
            logging.info("actions_handler()::FilesStore mode(level3) \'{0}\' command sent from user {1}({2})"
                         .format(message.text, message.from_user.full_name, message.from_user.id))

            if message.text == '⤴️На уровень выше':
                act.statements[message.from_user.id]["filesLevel"] = 3

            if not act.currentFolder(message.from_user.id):
                act.statements[message.from_user.id]["currentFolder"] = message.text[2:]
            files_list = db.get_files_from_folder(message.from_user.id, act.semester(message.from_user.id),
                                                  act.currentDiscipline(message.from_user.id),
                                                  act.currentFolder(message.from_user.id))

            # print("l3 ", act.statements[message.from_user.id])
            if files_list:
                kb = act.generateFilesKeyboard(files_list)
                act.fLevelUp(message.from_user.id)
                await message.answer(text(bold("Выберите желаемый файл:")), reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN_V2)
            else:
                act.reset(message.from_user.id)
                await message.answer("<Пусто>")

        # Вывод файлов/папок 4 уровень[страница с информацией о файле]
        elif act.filesLevel(message.from_user.id) == 4:
            logging.info("actions_handler()::FilesStore mode(level4) \'{0}\' command sent from user {1}({2})"
                         .format(message.text, message.from_user.full_name, message.from_user.id))
            file_record = db.get_file_record(message.from_user.id, act.semester(message.from_user.id),
                                             act.currentDiscipline(message.from_user.id),
                                             act.currentFolder(message.from_user.id),
                                             message.text[2:])
            if file_record:
                file_page = act.generateFilePage2(file_record)
                kb = act.FolderLevelUpKeyboard()
                act.fLevelUp(message.from_user.id)
                file_id = db.get_file(file_record[7])
                await message.answer(file_page, reply_markup=kb)
                await bot.send_document(message.from_user.id, file_id)

            else:
                act.reset(message.from_user.id)
                await message.answer("<Пусто>")

    # Выбор пути для загрузки
    elif act.isUploadMode(message.from_user.id):
        logging.info("actions_handler()::Upload mode \'{0}\' command sent from user {1}({2})"
                     .format(message.text, message.from_user.full_name, message.from_user.id))

        if act.semester(message.from_user.id) == 0 and message.text[0] in ('1', '2'):
            act.statements[message.from_user.id]["semester"] = int(message.text[0])
            disciplines_list = db.get_disciplines(message.from_user.id, act.semester(message.from_user.id))
            if disciplines_list:
                kb = act.generateDisciplinesKeyboard(disciplines_list, False)
                await message.answer(text(bold("Выберите желаемый предмет:")), reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN_V2)
            else:
                act.reset(message.from_user.id)
                await message.answer("Не удалось получить список дисциплин!")

        elif act.currentDiscipline(message.from_user.id) == "":
            act.statements[message.from_user.id]["currentDiscipline"] = message.text
            folders_list = db.get_folders_by_discipline(message.from_user.id, act.semester(message.from_user.id),
                                                        act.currentDiscipline(message.from_user.id))
            if folders_list:
                kb = act.generateFoldersKeyboard(folders_list, False)
                await message.answer(text(bold("Выберите желаемый раздел:")), reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN_V2)
            else:
                act.reset(message.from_user.id)
                await message.answer("Не удалось получить список разделов!")

        elif act.currentFolder(message.from_user.id) == "":
            act.statements[message.from_user.id]["currentFolder"] = message.text[2:]
            if (act.semester(message.from_user.id) != 0) and (act.currentDiscipline(message.from_user.id) != "") and (
                    db.folder_exists(act.currentFolder(message.from_user.id))):
                await message.answer("Файл будет загружен в \n{0} семестр\\{1}\\{2}\\".format(
                    act.semester(message.from_user.id), act.currentDiscipline(message.from_user.id),
                    act.currentFolder(message.from_user.id)))
                await message.answer("Размер загружаемого файла —  не более 20 Мб!")
                await message.answer("Ожидание отправки...")
            else:
                act.reset(message.from_user.id)
                await message.answer("Не найдена указанная папка!")

    # Выбор пути для удаления
    elif act.isDeleteMode(message.from_user.id):
        logging.info("actions_handler()::Delete mode \'{0}\' command sent from user {1}({2})"
                     .format(message.text, message.from_user.full_name, message.from_user.id))

        if act.semester(message.from_user.id) == 0 and message.text[0] in ('1', '2'):
            act.statements[message.from_user.id]["semester"] = int(message.text[0])
            disciplines_list = db.get_disciplines(message.from_user.id, act.semester(message.from_user.id))
            # print(act.semester(message.from_user.id), disciplines_list)
            if disciplines_list:
                kb = act.generateDisciplinesKeyboard(disciplines_list, False)
                await message.answer(text(bold("Выберите желаемый предмет:")), reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN_V2)
            else:
                act.reset(message.from_user.id)
                await message.answer("Не удалось получить список дисциплин!")

        elif act.currentDiscipline(message.from_user.id) == "":
            act.statements[message.from_user.id]["currentDiscipline"] = message.text
            folders_list = db.get_folders_by_discipline(message.from_user.id, act.semester(message.from_user.id),
                                                        act.currentDiscipline(message.from_user.id))
            if folders_list:
                kb = act.generateFoldersKeyboard(folders_list, False)
                await message.answer(text(bold("Выберите желаемый раздел:")), reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN_V2)
            else:
                act.reset(message.from_user.id)
                await message.answer("Не удалось получить список разделов!")

        elif act.currentFolder(message.from_user.id) == "":
            act.statements[message.from_user.id]["currentFolder"] = message.text[2:]
            files_list = db.get_files_from_folder(message.from_user.id, act.semester(message.from_user.id),
                                                  act.currentDiscipline(message.from_user.id),
                                                  act.currentFolder(message.from_user.id))
            if files_list:
                kb = act.generateFilesKeyboard(files_list, False)
                await message.answer(text(bold("Выберите желаемый файл:")), reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN_V2)
            else:
                act.reset(message.from_user.id)
                await message.answer("Не удалось получить список файлов!")

        else:
            fname = message.text[2:]
            file_record = db.get_file_record(message.from_user.id, act.semester(message.from_user.id),
                                             act.currentDiscipline(message.from_user.id),
                                             act.currentFolder(message.from_user.id),
                                             fname)
            if file_record:
                db.delete_file(message.from_user.id, act.semester(message.from_user.id),
                               act.currentDiscipline(message.from_user.id),
                               act.currentFolder(message.from_user.id), fname)
                await message.answer("Успешно удалено: \n{0} семестр\\{1}\\{2}\\{3}".format(
                    act.semester(message.from_user.id), act.currentDiscipline(message.from_user.id),
                    act.currentFolder(message.from_user.id), fname))
                act.reset(message.from_user.id)
            else:
                act.reset(message.from_user.id)
                await message.answer("Файл не найден!")

    # /mkdir
    elif act.isMkdirMode(message.from_user.id):
        logging.info("actions_handler()::Mkdir mode \'{0}\' command sent from user {1}({2})"
                     .format(message.text, message.from_user.full_name, message.from_user.id))

        if act.semester(message.from_user.id) == 0 and message.text[0] in ('1', '2'):
            act.statements[message.from_user.id]["semester"] = int(message.text[0])
            disciplines_list = db.get_disciplines(message.from_user.id, act.semester(message.from_user.id))
            # print(act.semester(message.from_user.id), disciplines_list)
            if disciplines_list:
                kb = act.generateDisciplinesKeyboard(disciplines_list, False)
                await message.answer(text(bold("Выберите желаемый предмет:")), reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN_V2)
            else:
                act.reset(message.from_user.id)
                await message.answer("Не удалось получить список дисциплин!")

        elif act.currentDiscipline(message.from_user.id) == "":
            act.statements[message.from_user.id]["currentDiscipline"] = message.text
            folders_list = db.get_folders_by_discipline(message.from_user.id, act.semester(message.from_user.id),
                                                        act.currentDiscipline(message.from_user.id))
            if folders_list:
                await message.answer(text(bold("Введите имя для новой папки: ")), parse_mode=ParseMode.MARKDOWN_V2)
            else:
                act.reset(message.from_user.id)
                await message.answer("Не удалось получить список разделов!")

        else:
            new_dir = message.text
            if db.folder_exists(new_dir):
                act.reset(message.from_user.id)
                await message.answer("Папка \"{0}\" уже существует!".format(new_dir))
            else:
                db.make_dir(message.from_user.id, act.semester(message.from_user.id),
                            act.currentDiscipline(message.from_user.id), new_dir)
                await message.answer("Успешно создано: \n{0} семестр\\{1}\\{2}\\".format(
                    act.semester(message.from_user.id), act.currentDiscipline(message.from_user.id),
                    new_dir))
                report = f"New dir {new_dir} created by: {message.from_user.full_name}({message.from_user.id})"
                await bot.send_message(AGENT_ID, report)
                act.reset(message.from_user.id)
    # /rmdir
    elif act.isRmdirMode(message.from_user.id):
        logging.info("actions_handler()::Mkdir mode \'{0}\' command sent from user {1}({2})"
                     .format(message.text, message.from_user.full_name, message.from_user.id))

        if act.semester(message.from_user.id) == 0 and message.text[0] in ('1', '2'):
            act.statements[message.from_user.id]["semester"] = int(message.text[0])
            disciplines_list = db.get_disciplines(message.from_user.id, act.semester(message.from_user.id))
            # print(act.semester(message.from_user.id), disciplines_list)
            if disciplines_list:
                kb = act.generateDisciplinesKeyboard(disciplines_list, False)
                await message.answer(text(bold("Выберите желаемый предмет:")), reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN_V2)
            else:
                act.reset(message.from_user.id)
                await message.answer("Не удалось получить список дисциплин!")

        elif act.currentDiscipline(message.from_user.id) == "":
            act.statements[message.from_user.id]["currentDiscipline"] = message.text
            folders_list = db.get_folders_by_discipline(message.from_user.id, act.semester(message.from_user.id),
                                                        act.currentDiscipline(message.from_user.id))
            if folders_list:
                kb = act.generateFoldersKeyboard(folders_list, False)
                await message.answer(text(bold("Выберите желаемый раздел:")), reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN_V2)
            else:
                act.reset(message.from_user.id)
                await message.answer("Не удалось получить список разделов!")

        else:
            dir_to_remove = message.text[2:]
            if not db.folder_exists(dir_to_remove):
                act.reset(message.from_user.id)
                await message.answer("Папка \"{0}\" не найдена!".format(dir_to_remove))
            else:
                db.delete_dir(message.from_user.id, act.semester(message.from_user.id),
                              act.currentDiscipline(message.from_user.id), dir_to_remove)
                await message.answer("Успешно удалено: \n{0} семестр\\{1}\\{2}\\".format(
                    act.semester(message.from_user.id), act.currentDiscipline(message.from_user.id),
                    dir_to_remove))
                report = f"Dir {dir_to_remove} is deleted by: {message.from_user.full_name}({message.from_user.id})"
                await bot.send_message(AGENT_ID, report)
                act.reset(message.from_user.id)

    else:
        logging.info("actions_handler():: UNKNOWN \'{0}\' command sent from user {1}"
                     .format(message.text, message.from_user.full_name))
        await message.answer("Неизвестная команда!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
