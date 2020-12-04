import os
import config
import asyncio
import logging
import hashlib
from aiogram import Bot

from dbManager import DbManager

bot = Bot(token=config.API_TOKEN)
MY_ID = 231905851
db = DbManager('db.db')

logging.basicConfig(format=u'%(filename)s [ LINE:%(lineno)+3s ]#%(levelname)+8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

DOCS_PATH = "G:\\Проектная деятельность\\upload2"
course = 2
group = 9
semester = 2


async def uploadMediaFiles():
    for discipline_name in os.listdir(DOCS_PATH):
        for dir_name in os.listdir(os.path.join(DOCS_PATH, discipline_name)):
            for fname in os.listdir(os.path.join(DOCS_PATH, discipline_name, dir_name)):
                if db.file_exists(fname, discipline_name, dir_name):
                    logging.info(f'{fname} already exists in the database, skipping...')
                    continue
                logging.info(f'Started processing {fname}')
                folder_path = os.path.join(DOCS_PATH, discipline_name, dir_name)
                with open(os.path.join(folder_path, fname), 'rb') as file:
                    try:
                        msg = await bot.send_document(MY_ID, file, disable_notification=True)
                        file_id = getattr(msg, 'document').file_id
                        db.add_file(file_id, fname, course, group, semester, discipline_name, dir_name, MY_ID)
                        logging.info(f'Successfully uploaded and saved to DB file {fname} with id {file_id}')
                    except Exception as e:
                        logging.error('Couldn\'t upload {}. Error is {}'.format(fname, e))


ioloop = asyncio.get_event_loop()
tasks = [ioloop.create_task(uploadMediaFiles())]
wait_tasks = asyncio.wait(tasks)
ioloop.run_until_complete(wait_tasks)
ioloop.close()
db.close()
