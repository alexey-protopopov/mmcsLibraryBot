from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton

directions = ("ПМИ", "Математика/Механика и математическое моделирование",
              "Theoretical Computer Science and Information Technologies", "ФИИТ", "Педагогическое образование")

course2 = {1: directions[0], 2: directions[0], 3: directions[0], 4: directions[0], 45: directions[0],
           5: directions[1],
           57: directions[1], 6: directions[2], 7: directions[3], 8: directions[3], 9: directions[3],
           10: directions[4],
           11: directions[4], 12: directions[4], 13: directions[4]}


class Actions:
    registrationStarted = False
    searchStarted = False
    filesMode = False
    search_pages = []
    filesLevel = 0
    semester = 0
    currentDiscipline = ""
    currentFolder = ""

    def startReg(self):
        self.registrationStarted = True

    def stopReg(self):
        self.registrationStarted = False

    def startSearch(self):
        self.searchStarted = True

    def stopSearch(self):
        self.searchStarted = False

    def startFilesMode(self):
        self.filesMode = True

    def stopFilesMode(self):
        self.filesMode = False

    def fLevelUp(self):
        if self.filesLevel in range(0, 4):
            self.filesLevel += 1

    def fLevelDown(self):
        if self.filesLevel in range(1, 5):
            self.filesLevel -= 1

    def reset(self):
        self.searchStarted = False
        self.registrationStarted = False
        self.filesMode = False
        self.search_pages = []
        self.filesLevel = 0
        self.semester = 0
        self.currentDiscipline = ""
        self.currentFolder = ""

    @staticmethod
    def generateFilePage(file):
        page = f"Название: {file[1]}\nПредмет: {file[5]}, раздел: {file[6]}.\n{file[2]} курс {course2[file[3]]}, " \
               f"{file[4]} семестр.\nСкачать файл: /download{file[7]}\n"
        return page

    def generateSearchPage(self, resp):
        for file in resp:
            try:
                page = self.generateFilePage(file)
                self.search_pages.append(page)
            except IndexError:
                return "Ничего не найдено."
        if len(self.search_pages) == 0:
            return "Ничего не найдено."
        return self.search_pages

    @staticmethod
    def generateDisciplinesKeyboard(disciplines):
        disciplines_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        up = KeyboardButton('⤴️На уровень выше')
        disciplines_kb.add(up)
        for d in disciplines:
            button = KeyboardButton(d)
            disciplines_kb.add(button)
        return disciplines_kb

    @staticmethod
    def generateFoldersKeyboard(folders):
        folders_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        up = KeyboardButton('⤴️На уровень выше')
        folders_kb.add(up)
        for folder in folders:
            button = KeyboardButton('📁 ' + folder)
            folders_kb.add(button)
        return folders_kb

    @staticmethod
    def generateFilesKeyboard(files):
        files_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        up = KeyboardButton('⤴️На уровень выше')
        files_kb.add(up)
        for file in files:
            button = KeyboardButton('📘 ' + file[1])
            files_kb.add(button)
        return files_kb

    @staticmethod
    def semestersKeyboard():
        button1 = KeyboardButton('1 семестр')
        button2 = KeyboardButton('2 семестр')
        semester_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(
            button1, button2)
        return semester_kb

    @staticmethod
    def FolderLevelUpKeyboard():
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        up = KeyboardButton('⤴️На уровень выше')
        kb.add(up)
        return kb
