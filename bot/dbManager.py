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

    def get_subscriptions(self, status=True):
        """Получаем всех активных подписчиков бота"""
        with self.connection:
            return self.cursor.execute("SELECT * FROM `subscriptions` WHERE `status` = ?", (status,)).fetchall()

    def subscriber_exists(self, user_id):
        """Проверяем, есть ли уже юзер в базе"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `subscriptions` WHERE `user_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_subscriber(self, user_id, status, course, group):
        """Добавляем нового подписчика"""
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO `subscriptions` (`user_id`, `access_level`, `course`,`group`) VALUES(?,?,?,?)",
                (user_id, 0, course, group))

    def delete_subscriber(self, user_id):
        """Удаляем подписчика"""
        with self.connection:
            return self.cursor.execute('DELETE FROM `subscriptions` WHERE `user_id` = ?', (user_id,)).fetchall()

    def update_subscription(self, user_id, status):
        """Обновляем статус подписки пользователя"""
        with self.connection:
            return self.cursor.execute("UPDATE `subscriptions` SET `status` = ? WHERE `user_id` = ?", (status, user_id))

    def get_user_info(self, user_id):
        """Получаем всю информацию о пользователе"""
        with self.connection:
            return self.cursor.execute("SELECT * FROM `subscriptions` WHERE `user_id` = ?", (user_id,)).fetchone()

    def get_disciplines(self, user_id, semester):
        """Получаем все дисциплины пользователя"""
        with self.connection:
            user_data = self.get_user_info(user_id)
            if not user_data:
                return []
            else:
                groups = course22.keys()
                for direction in groups:
                    if user_data[4] in direction:
                        break

                result = self.cursor.execute('SELECT DISTINCT `discipline_name` FROM `files` WHERE `course` = ? AND `group` = ? AND `semester` = ?',
                                             (user_data[3], direction[-1], semester)).fetchall()
                return [v[0] for v in result]

    def file_exists(self, fname, discipline_name, dir_name):
        """Проверяем, есть ли уже файл в базе"""
        with self.connection:
            result = self.cursor.execute(
                'SELECT * FROM `files` WHERE `fname` = ? AND `discipline_name` = ? AND `dir_name` = ?',
                (fname, discipline_name, dir_name)).fetchall()
            return bool(len(result))

    def add_file(self, file_id, fname, course, group, semester, discipline_name, dir_name):
        """Добавление файла в db"""
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO `files` (`file_id`, `fname`, `course`,`group`,`semester`,`discipline_name`,`dir_name`) VALUES(?,?,?,?,?,?,?)",
                (file_id, fname, course, group, semester, discipline_name, dir_name))

    def get_file(self, num_id):
        """Получение id файла"""
        with self.connection:
            result = self.cursor.execute('SELECT `file_id` FROM `files` WHERE `id` = ?', (num_id,)).fetchall()
            return result[0][0]

    def search_by_name(self, fname):
        """Поиск по названию"""
        resp = []
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `files`').fetchall()
            for file in result:
                if file[1].lower().find(fname.lower()) != -1:
                    resp.append(file)
            return resp

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()


# db = DbManager("db.db")
# print(db.get_disciplines(231905851))
# db.get_disciplines(231905850)
# a = db.search_by_name("Судоплатов")
# act = Actions()
# act.generateSearchPage(a)
# db.get_file("CS292-1 Теория погрешностей.pdf")
