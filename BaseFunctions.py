from random_user_agent.params import SoftwareName, OperatingSystem
from selenium.webdriver.support import expected_conditions as EC
from random_user_agent.user_agent import UserAgent
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from sys import platform
from time import sleep

import logging
import json
import re
import os

#==========================================================================================#
# >>>>> КЛАССЫ <<<<< #
#==========================================================================================#

# Вывод в консоль цветного текста.
class ColoredPrinter(object):
	
	# Конструктор.
	def __init__(self):
		# Базовые цвета.
		self.BLACK = "0"
		self.RED = "1"
		self.GREEN = "2"
		self.YELLOW = "3"
		self.BLUE = "4"
		self.PURPLE = "5"
		self.CYAN = "6"
		self.WHITE = "7"
		# Переключатель: возвращать ли стандартные настройки после каждого вывода.
		self.ResetStylesAfterPrint = True
		# Переключатель: переход на новую строку после вывода.
		self.NewLineAfterPrint = False

	# Вывод в консоль.
	def Print(self, Text: str(), TextColor: str(), BackgroundColor: str() = ""):
		# Если передан цвет для фота, то создать соответствующий модификатор.
		if BackgroundColor != "":
			BackgroundColor = "\033[4" + BackgroundColor + "m"
		# Генерация модификатора цвета текста.
		TextColor = "\033[3" + TextColor + "m"
		# Создание результирующей строки со стилями: цветового модификатора, модификатора фона, текста.
		StyledText = TextColor + BackgroundColor + Text
		# Если указано, добавить модификатор сброса стилей после вывода.
		if self.ResetStylesAfterPrint == True:
			StyledText = StyledText + "\033[0m"
		# Вывод в консоль и установка параметра перехода на норвую строку.
		if self.NewLineAfterPrint == True:
			print(StyledText, end = "")
		else:
			print(StyledText)

#==========================================================================================#
# >>>>> БАЗОВЫЕ ФУНКЦИИ <<<<< #
#==========================================================================================#

# Регулярное выражение фильтрации тегов HTML.
TagsHTML = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

# Выключает ПК: работает на Windows и Linux.
def Shutdown():
	if platform == "linux" or platform == "linux2":
		os.system('sudo shutdown now')
	elif platform == "win32":
		os.system("shutdown /s")

# Удаляет теги HTML из строки.
def RemoveHTML(TextHTML):
  CleanText = re.sub(TagsHTML, '', str(TextHTML))

  return str(CleanText)

# Удаляет из строки символы: новой строки, табуляции, пробелы из начала и конца.
def RemoveSpaceSymbols(Text):
	Text = Text.replace('\n', '')
	Text = Text.replace('\t', '')
	Text = ' '.join(Text.split())

	return Text.strip()

# Заменяет символ новой строки на запятую с пробелом.
def ReplaceEndlToComma(Text):
	Text = Text.strip()
	Text = Text.replace('\n', ', ')

	return Text

# Преобразует литеральное число в int.
# Примечание: используется только для вычисления количества оценок.
def LiteralToInt(String):
	if String.isdigit():
		return int(String)
	else:
		Number = float(String[:-1]) * 1000
	return int(Number)

# Очищает консоль.
def Cls():
	os.system('cls' if os.name == 'nt' else 'clear')

# Выводит прогресс процесса.
def PrintProgress(String, Current, Total):
	Cls()
	print(String, " ", Current, " / ", Total)

# Удаляет запросы из URL.
def RemoveArgumentsFromURL(URL):
	return str(URL).split('?')[0]

# Усекает число до определённого количества знаков после запятой.
def ToFixedFloat(FloatNumber, Digits = 0):
	return float(f"{FloatNumber:.{Digits}f}")

# Проевращает число секунд в строку-дескриптор времени по формату [<x> hours <y> minuts <z> seconds].
def SecondsToTimeString(Seconds):
	# Количество часов.
	Hours = int(Seconds / 3600.0)
	Seconds -= Hours * 3600
	# Количество минут.
	Minutes = int(Seconds / 60.0)
	Seconds -= Minutes * 60
	# Количество секунд.
	Seconds = ToFixedFloat(Seconds, 2)
	# Строка-дескриптор времени.
	TimeString = ""

	# Генерация строки.
	if Hours > 0:
		TimeString += str(Hours) + " hours "
	if Minutes > 0:
		TimeString += str(Minutes) + " minutes "
	if Seconds > 0:
		TimeString += str(Seconds) + " seconds"

	return TimeString

# Возвращает случайное значение заголовка User-Agent.
def GetRandomUserAgent():
	SoftwareNames = [SoftwareName.CHROME.value]
	OperatingSystems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   
	UserAgentRotator = UserAgent(software_names = SoftwareNames, operating_systems = OperatingSystems, limit = 100)

	return str(UserAgentRotator.get_random_user_agent()).strip('"')

# Удаляет повторы значений из словаря.
def RemoveDuplicatesFromDict(Dictionary: dict()):
	return {v:k for k,v in {Dictionary[k]:k for k in reversed(list(Dictionary))}.items()}

# Инвертирует порядок элементов словаря.
def ReverseDict(Dictionary: dict()):
	# Список ключей.
	Keys = list(Dictionary.keys())
	# Инвертирование списка ключей.
	Keys.reverse()
	# Инвертированный словарь.
	ReversedDict = dict()

	# Запись значений в обратном порядке.
	for InObj in Keys:
		ReversedDict[InObj] = Dictionary[InObj]

	return ReversedDict

#==========================================================================================#
# >>>>> СКАНИРОВАНИЕ ОБНОВЛЕНИЙ <<<<< #
#==========================================================================================#

# Получает количество страниц каталога.
def GetPagesCount(Browser):
	# Переход на страницу с обновлениями.
	Browser.get("https://hentaichan.live/manga/new")
	# HTML-код страницы после полной загрузки.
	BodyHTML = Browser.execute_script("return document.body.innerHTML;")
	# Парсинг страницы обновлений.
	Soup = BeautifulSoup(BodyHTML, "lxml")
	# Блок навигации по страницам.
	Pages = Soup.find_all("span", {"style" : "line-height: 28px;"})
	# Парсинг блока навигации.
	SmallSoup = BeautifulSoup(str(Pages), "lxml")
	# Ссылки на страницы.
	PagesLinks = SmallSoup.find_all("a")
	# Количество страниц (добавляется 1 для компенсации отсутствия в списке первой страницы).
	PagesCount = len(PagesLinks) + 1

	return PagesCount

# Возвращает ID последнего определения главы.
def GetLastChapterDefinitionID() -> str:
	# Определения слайдов.
	Definitions = None
	# ID последнего определения главы.
	ChapterID = ""

	# Проверка существования файла.
	if os.path.exists("#Definitions.json") == True:
		# Отктрытие файла.
		with open("#Definitions.json") as FileRead:
			# Парсинг JSON.
			Definitions = json.load(FileRead)

	# Если в определениях есть ключи, то записать первое значение.
	if len(Definitions.keys()) > 0:
		ChapterID = list(Definitions.keys())[0]

	return ChapterID

#==========================================================================================#
# >>>>> ПАРСИНГ ГЛАВ <<<<< #
#==========================================================================================#

# Вход на сайт.
def LogIn(Browser, Settings: dict):
	# Проверка наличия логина и пароля.
	if Settings["login"] != "" and Settings["password"] != "":
		# Переход на главную страницу слайда.
		Browser.get("https://hentaichan.live")
		# Поиск поля ввода логина.
		EmailInput = Browser.find_element(By.CSS_SELECTOR , "input[name=\"login_name\"]")
		# Поиск поля ввода пароля.
		PasswordInput = Browser.find_element(By.CSS_SELECTOR , "input[name=\"login_password\"]")
		# Ввод логина.
		EmailInput.send_keys(Settings["login"])
		# Ввод пароля.
		PasswordInput.send_keys(Settings["password"])
		# Клик по кнопке входа.
		Browser.find_element(By.CSS_SELECTOR, "input[name=\"image\"]").click()
	else:
		# Запись в лог сообщения об отсутствующем пароле.
		logging.warning("Login or password wasn't found. Authorization skipped.")

# Генерирует полный алиас главы на основе определения.
def BuildChapterLinkFromDefinition(Settings, ChapterID: str) -> str:
	# Определения глав.
	Definitions = None
	# URL главы.
	ChapterURL = ""

	# Проверка существования файла.
	if os.path.exists("#Definitions.json"):
		# Открытие файла определений.
		with open("#Definitions.json", encoding = "utf-8") as FileRead:
			# Чтение JSON.
			Definitions = json.load(FileRead)
	else:
		raise FileNotFoundError("\"#Definitions.json\" isn't founded.")

	# Проверка наличия соответствующего ключа и построение URL.
	if ChapterID in Definitions.keys():
		ChapterURL = ChapterID + "-" + Definitions[ChapterID]["slug"] + ".html"
	else:
		raise KeyError("Key wasn't found in the \"#Definitions.json\" file.")

	return ChapterURL

# Проверяет наличие размеров слайдов и возвращает количество ошибок.
def CheckSlidesSizesPresence(SlidesList) -> int:
	# Количество слайдов без размеров.
	BasSlidesCount = 0

	# Для каждого слайда проверить наличие размеров.
	for Slide in SlidesList:
		if Slide["width"] == None or Slide["height"] == None:
			BasSlidesCount += 1

	return BasSlidesCount

# Получает список слайдов и сохраняет их в файл.
def GetSlides(Browser, Settings: dict, ChapterFullSlug: str, SlidesCount: int, InFuncMessage: str):
	# Список прямых ссылок на слайды.
	SlidesList = []
	# ID главы.
	ChapterID = ChapterFullSlug.split('-')[0]
	# Частичный алиас главы.
	ChapterSlug = ChapterFullSlug.replace(".html", "").replace(ChapterID + "-", "")
	# Запись в лог сообщения о парсинге конкретной главы.
	logging.info("Chapter: " + ChapterID + " (\"" + ChapterSlug + "\") parcing started...")

	# Получение прямой ссылки на каждый слайд.
	for SlideIndex in range(1, SlidesCount + 1):
		# Очистка консоли.
		Cls()
		# Вывод в консоль прогресса.
		print(InFuncMessage + "Parcing chapter " + ChapterID + ": " + str(SlideIndex) + " / " + str(SlidesCount + 1) + ".")
		# Переход на страницу слайда.
		Browser.get("https://hentaichan.live/online/" + ChapterFullSlug + "?page=" + str(SlideIndex))
		# HTML-код страницы после полной загрузки.
		BodyHTML = Browser.execute_script("return document.body.innerHTML;")
		# Парсинг HTML-кода страницы.
		Soup = BeautifulSoup(BodyHTML, "lxml")
		# Поиск блока со слайдами.
		SlideImageBlock = Soup.find("img", {"style": "max-width:1000px;background-color:white;"})
		# Структура слайда.
		SlideInfo = {}
		SlideInfo["link"] = ""
		SlideInfo["width"] = None
		SlideInfo["height"] = None
		# Получение прямой ссылки на слайд.
		SlideInfo["link"] = SlideImageBlock["src"]

		# Получение размеров слайдов, если таковой режим включен.
		if Settings["getting-slide-sizes"] == True:

			# Получение ширины слайда.
			SlideInfo["width"] = Browser.execute_script('''
				var img = new Image();
				img.src = arguments[0]
				return img.width
			''', 
			SlideInfo["link"])

			# Повышение высоты слайда.
			SlideInfo["height"] = Browser.execute_script('''
				var img = new Image();
				img.src = arguments[0]
				return img.height
			''', 
			SlideInfo["link"])

		# Запись прямой ссылки на слайд.
		SlidesList.append(SlideInfo)
		# Выжидание интервала перелистывания.
		sleep(Settings["delay"])

	# Проверка наличия размеров слайдов, если таковая функция включена.
	if Settings["getting-slide-sizes"] == True:
		# Количество плохих слайдов.
		BadSlidesCount = CheckSlidesSizesPresence(SlidesList)

		# Если есть ошибки, записать их в лог.
		if BadSlidesCount > 0:
			# Запись в лог сообщения об отсутствующих размерах слайдов.
			logging.warning("Chapter: " + ChapterID + " (\"" + ChapterSlug + "\") have bad slides: " + str(BadSlidesCount) + ".")
		else:
			# Запись в лог сообщения об успешном получении всех размеров слайдов.
			logging.info("Chapter: " + ChapterID + " (\"" + ChapterSlug + "\") sizing successfully.")

	# Запись в лог сообщения о завершении парсинга.
	logging.info("Chapter: " + ChapterID + " (\"" + ChapterSlug + "\") parced. Completed.")

	# Сохранение файла.
	with open("chapters/" + ChapterID + ".json", "w", encoding = "utf-8") as FileWrite:
		json.dump(SlidesList, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))

