import sqlite3

from actions import directions

course22 = {(1, 2, 3, 4, 45): directions[0], (1, 57): directions[1], (6,): directions[2], (7, 8, 9): directions[3],
            (10, 11, 12, 13): directions[4]}


class DbManager:
    # поле status я удалил, надо будет исправить
    def __init__(self, database):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def subscriber_exists(self, user_id):
        """Проверяем, есть ли уже юзер в базе"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `subscriptions` WHERE `user_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def folder_exists(self, dir_name):
        """Проверяем, есть ли указанная папка в базе"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `files` WHERE `dir_name` = ?', (dir_name,)).fetchall()
            return bool(len(result))

    def file_exists(self, fname, discipline_name, dir_name):  # TODO: расширить
        """Проверяем, есть ли уже файл в базе"""
        with self.connection:
            result = self.cursor.execute(
                'SELECT * FROM `files` WHERE `fname` = ? AND `discipline_name` = ? AND `dir_name` = ?',
                (fname, discipline_name, dir_name)).fetchall()
            return bool(len(result))

    def add_subscriber(self, user_id, status, course, group):
        """Добавляем нового подписчика"""
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO `subscriptions` (`user_id`, `access_level`, `course`,`group`) VALUES(?,?,?,?)",
                (user_id, 0, course, group))

    def set_admin(self, user_id):
        """Назначаем пользователя админом"""
        with self.connection:
            return self.cursor.execute('UPDATE `subscriptions` SET `access_level` = 1 WHERE `user_id` = ?',
                                       (user_id,)).fetchall()

    def delete_subscriber(self, user_id):
        """Удаляем подписчика"""
        with self.connection:
            return self.cursor.execute('DELETE FROM `subscriptions` WHERE `user_id` = ?', (user_id,)).fetchall()

    def delete_file(self, user_id, semester, discipline_name, dir_name, fname):
        """Удаляем файл"""
        course = self.get_user_info(user_id)[3]
        group = self.get_db_group(user_id)
        with self.connection:
            return self.cursor.execute(
                'DELETE FROM `files` WHERE `course` = ? AND `group` = ? AND `semester` = ? AND `fname` = ? AND `discipline_name` = ? AND `dir_name` = ?',
                (course, group, semester, fname, discipline_name, dir_name)).fetchall()

    def get_user_info(self, user_id):
        """Получаем всю информацию о пользователе"""
        with self.connection:
            return self.cursor.execute("SELECT * FROM `subscriptions` WHERE `user_id` = ?", (user_id,)).fetchone()

    def get_db_group(self, user_id):
        with self.connection:
            user_data = self.get_user_info(user_id)
            if not user_data:
                return []
            else:
                groups = course22.keys()
                for direction in groups:
                    if user_data[4] in direction:
                        break
                return direction[-1]

    def get_disciplines(self, user_id, semester):
        """Получаем все дисциплины пользователя"""
        with self.connection:
            user_data = self.get_user_info(user_id)
            group = self.get_db_group(user_id)
            if not group or not user_data:
                print("get_disciplines not group or not user_data")
                return []
            else:
                result = self.cursor.execute(
                    'SELECT DISTINCT `discipline_name` FROM `files` WHERE `course` = ? AND `group` = ? AND `semester` = ?',
                    (user_data[3], group, semester)).fetchall()
                return [v[0] for v in result]

    def get_folders_by_discipline(self, user_id, semester, discipline_name):
        """Получаем все разделы для дисциплины пользователя"""
        with self.connection:
            user_data = self.get_user_info(user_id)
            group = self.get_db_group(user_id)
            if not group or not user_data:
                return []
            else:
                result = self.cursor.execute(
                    'SELECT DISTINCT `dir_name` FROM `files` WHERE `course` = ? AND `group` = ? AND `semester` = ? AND `discipline_name` = ?',
                    (user_data[3], group, semester, discipline_name)).fetchall()
                return [v[0] for v in result]

    def make_dir(self, user_id, semester, discipline_name, new_dir):
        """Создаём новую папку"""
        course = self.get_user_info(user_id)[3]
        group = self.get_db_group(user_id)
        if not group or not course:
            return []
        else:
            self.add_file("placeholder", "placeholder", course, group, semester, discipline_name, new_dir, "placeholder")

    def get_file_record(self, user_id, semester, discipline_name, dir_name, fname):
        """Получаем запись файла из бд, c определённым курсом,группой, названием, семестром"""
        with self.connection:
            user_data = self.get_user_info(user_id)
            group = self.get_db_group(user_id)
            if not group or not user_data:
                return []
            else:
                result = self.cursor.execute(
                    'SELECT * FROM `files` WHERE `course` = ? AND `group` = ? AND `semester` = ? AND `discipline_name` = ? AND `dir_name` = ? AND `fname` = ?',
                    (user_data[3], group, semester, discipline_name, dir_name, fname)).fetchone()
                if result[0] != "placeholder":
                    return result
                else:
                    return ()

    def add_file(self, file_id, fname, course, group, semester, discipline_name, dir_name, owner):
        """Добавление файла в db"""
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO `files` (`file_id`, `fname`, `course`,`group`,`semester`,`discipline_name`,`dir_name`,`owner`) VALUES(?,?,?,?,?,?,?,?)",
                (file_id, fname, course, group, semester, discipline_name, dir_name, owner))

    def get_file(self, num_id):
        """Получение id файла"""
        with self.connection:
            result = self.cursor.execute('SELECT `file_id` FROM `files` WHERE `id` = ?', (num_id,)).fetchall()
            return result[0][0]

    def get_files_from_folder(self, user_id, semester, discipline_name, dir_name):
        user_data = self.get_user_info(user_id)
        group = self.get_db_group(user_id)
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `files` WHERE `course` = ? AND `group` = ? AND `semester` = ? '
                                         'AND `discipline_name` = ? AND `dir_name` = ? AND `file_id` != ?',
                                         (user_data[3], group, semester, discipline_name, dir_name, "placeholder")).fetchall()
            return result

    def search_by_name(self, fname):
        """Поиск по названию"""
        resp = []
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `files`').fetchall()
            for file in result:
                if file[1].lower().find(fname.lower()) != -1 and file[1].lower() != "placeholder":
                    resp.append(file)
            return resp

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()
