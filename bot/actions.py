from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton

directions = ("ПМИ", "Математика/Механика и математическое моделирование",
              "Theoretical Computer Science and Information Technologies", "ФИИТ", "Педагогическое образование")

course2 = {1: directions[0], 2: directions[0], 3: directions[0], 4: directions[0], 45: directions[0],
           5: directions[1],
           57: directions[1], 6: directions[2], 7: directions[3], 8: directions[3], 9: directions[3],
           10: directions[4],
           11: directions[4], 12: directions[4], 13: directions[4]}

inline_btn_right = InlineKeyboardButton('➡️', callback_data='right')
inline_btn_left = InlineKeyboardButton('⬅️', callback_data='left')


class Actions:
    statements = {}

    # registrationStarted = False
    # searchStarted = False
    # filesMode = False
    # search_pages = []
    # search_pages_count = 0
    # search_pages_position = 1
    # filesLevel = 0
    # semester = 0
    # currentDiscipline = ""
    # currentFolder = ""

    def uid_check(self, uid):
        if self.statements.get(uid) is None:
            self.reset(uid)

    def registrationStarted(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["registrationStarted"]

    def search_pages_position(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["search_pages_position"]

    def search_pages_count(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["search_pages_count"]

    def filesLevel(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["filesLevel"]

    def currentFolder(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["currentFolder"]

    def semester(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["semester"]

    def currentDiscipline(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["currentDiscipline"]

    def searchStarted(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["searchStarted"]

    def isFilesMode(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["filesMode"]

    def isUploadMode(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["uploadStarted"]

    def isMkdirMode(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["mkdirStarted"]

    def isRmdirMode(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["rmdirStarted"]

    def isDeleteMode(self, uid):
        self.uid_check(uid)
        return self.statements[uid]["deleteStarted"]

    def startReg(self, uid):
        self.uid_check(uid)
        self.statements[uid]["registrationStarted"] = True

    def stopReg(self, uid):
        self.uid_check(uid)
        self.statements[uid]["registrationStarted"] = False

    def startSearch(self, uid):
        self.uid_check(uid)
        self.statements[uid]["searchStarted"] = True

    def startUpload(self, uid):
        self.uid_check(uid)
        self.statements[uid]["uploadStarted"] = True

    def startDelete(self, uid):
        self.uid_check(uid)
        self.statements[uid]["deleteStarted"] = True

    def startMkdir(self, uid):
        self.uid_check(uid)
        self.statements[uid]["mkdirStarted"] = True

    def startRmdir(self, uid):
        self.uid_check(uid)
        self.statements[uid]["rmdirStarted"] = True

    def stopUpload(self, uid):
        self.uid_check(uid)
        self.statements[uid]["uploadStarted"] = False

    def stopSearch(self, uid):
        self.uid_check(uid)
        self.statements[uid]["searchStarted"] = False

    def startFilesMode(self, uid):
        self.uid_check(uid)
        self.statements[uid]["filesMode"] = True
        self.statements[uid]["filesLevel"] = 1

    def stopFilesMode(self, uid):
        self.uid_check(uid)
        self.statements[uid]["filesMode"] = False

    def fLevelUp(self, uid, text=""):
        self.uid_check(uid)
        # if text == '⤴️На уровень выше':
        # return
        if self.statements[uid]["filesLevel"] in range(0, 5):
            self.statements[uid]["filesLevel"] += 1

    def reset(self, uid):
        self.statements[uid] = {"registrationStarted": False, "searchStarted": False, "filesMode": False,
                                "search_pages": [], "search_pages_count": 0, "search_pages_position": 1,
                                "filesLevel": 0,
                                "semester": 0, "currentDiscipline": "", "currentFolder": "", "uploadStarted": False,
                                "deleteStarted": False, "mkdirStarted": False, "rmdirStarted": False}

    @staticmethod
    def generateFilePage(file):
        page = f"Название: {file[1]}\nПредмет: {file[5]}, раздел: {file[6]}.\n{file[2]} курс {course2[file[3]]}, " \
               f"{file[4]} семестр.\nСкачать файл: /download{file[7]}\n"
        return page

    @staticmethod
    def generateFilePage2(file):
        page = f"Название: {file[1]}\nПредмет: {file[5]}, раздел: {file[6]}.\n{file[2]} курс {course2[file[3]]}, " \
               f"{file[4]} семестр.\n"
        return page

    def generateSearchPage(self, resp, uid):
        for file in resp:
            try:
                page = self.generateFilePage(file)
                self.statements[uid]["search_pages"].append(page)
            except IndexError:
                return []
        search_pages_len = len(self.statements[uid]["search_pages"])
        if search_pages_len == 0:
            return []
        elif search_pages_len % 4 == 0:
            self.statements[uid]["search_pages_count"] = search_pages_len // 4
        else:
            self.statements[uid]["search_pages_count"] = search_pages_len // 4 + 1
        return self.statements[uid]["search_pages"]

    @staticmethod
    def generateDisciplinesKeyboard(disciplines, toggleUpButton=True):
        disciplines_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        if toggleUpButton:
            up = KeyboardButton('⤴️На уровень выше')
            disciplines_kb.add(up)
        for d in disciplines:
            button = KeyboardButton(d)
            disciplines_kb.add(button)
        return disciplines_kb

    @staticmethod
    def generateFoldersKeyboard(folders, toggleUpButton=True):
        folders_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        if toggleUpButton:
            up = KeyboardButton('⤴️На уровень выше')
            folders_kb.add(up)
        for folder in folders:
            button = KeyboardButton('📁 ' + folder)
            folders_kb.add(button)
        return folders_kb

    @staticmethod
    def generateFilesKeyboard(files, toggleUpButton=True):
        files_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        if toggleUpButton:
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

    @staticmethod
    def searchKeyboardBegin():
        inline_kb1 = InlineKeyboardMarkup().add(inline_btn_right)
        return inline_kb1

    @staticmethod
    def searchKeyboardEnd():
        inline_kb2 = InlineKeyboardMarkup().add(inline_btn_left)
        return inline_kb2

    @staticmethod
    def searchKeyboardMid():
        inline_kb3 = InlineKeyboardMarkup(row_width=2).add(inline_btn_left, inline_btn_right)
        # inline_kb3.row(inline_btn_left, inline_btn_right)
        return inline_kb3
