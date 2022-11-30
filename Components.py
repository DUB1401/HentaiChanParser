from bs4 import BeautifulSoup
from time import sleep

import logging
import json
import os

# >>>>> БАЗОВЫЕ ФУНКЦИИ <<<<< #
from BaseFunctions import ColoredPrinter
from BaseFunctions import RemoveHTML
from BaseFunctions import Cls

# >>>>> ПАРСИНГ ГЛАВ <<<<< #
from BaseFunctions import BuildChapterLinkFromDefinition
from BaseFunctions import GetSlides

# Сканирование обновлений сайта.
def ScanTitles(Browser, Settings, Page, InFuncMessage, Delay = False):
	# Очистка содержимого консоли.
	Cls()
	# Вывод прогресса.
	print(InFuncMessage)
	# Вычисление смещения страницы.
	Offset = 20 * int(Page) - 20
	# Переход на страницу с обновлениями.
	Browser.get("https://hentaichan.live/manga/new?offset=" + str(Offset))
	# HTML-код страницы после полной загрузки.
	BodyHTML = Browser.execute_script("return document.body.innerHTML;")
	# Парсинг страницы обновлений.
	Soup = BeautifulSoup(BodyHTML, "lxml")
	# Заголовки тайтлов на странице.
	TitlesHeaders = Soup.find_all("h2")
	# Список ссылок на тайтлы.
	TitlesLinks = []
	# Словарь определений для записи.
	TitlesDefinitions = {}
	# Ответ функции: найдены ли совпадения и количество новых опеределений.
	Answer = { "already-exists" : False, "new-definitions-count" : 0 }
	# Загруженные определения, если таковые имеются.
	Definitions = None

	# Проверка существования файла.
	if os.path.exists("#Definitions.json"):
		# Чтение файла.
		with open("#Definitions.json") as FileRead:
			Definitions = json.load(FileRead)
			# Проверка успешной загрузки файла.
			if Definitions == None:
				# Запись в лог ошибки о невозможности прочитать битый файл.
				logging.error("Unable to read \"#Definitions.json\". File is broken.")
			else:
				TitlesDefinitions = Definitions

	# Получение ссылок на главы.
	for Header in TitlesHeaders:
		# Парсер заголовка.
		SmallSoup = BeautifulSoup(str(Header), "lxml")
		# Получение ссылки на главу без относительного пути и расширения.
		TitlesLinks.append(SmallSoup.find("a")["href"].replace("/manga/", "").replace(".html", ""))

	# Генерация словаря определений.
	for Link in TitlesLinks:
		# ID главы.
		ChapterID = Link.split('-')[0]
		# Алиас главы.
		ChapterSlug = Link.replace(ChapterID + "-", "")
		# Проверка наличия главы в файле определений, и, если таковой нет, инкремент новых определений.
		if ChapterID in TitlesDefinitions.keys():
			Answer["already-exists"] = True
		else:
			# Инкремент количества новых определений.
			Answer["new-definitions-count"] += 1
			# Запись в лог сообщения о новом определении.
			logging.info("Add definition. ID: " + ChapterID + ". Slug: \"" + ChapterSlug + "\".")
		# Создание ключа с пустым словарём.
		TitlesDefinitions[ChapterID] = {}
		# Запись значений определения.
		TitlesDefinitions[ChapterID]["slug"] = ChapterSlug

	# Сортировка по убыванию ID глав.
	TitlesDefinitions = dict(sorted(TitlesDefinitions.items(), key = lambda x: int(x[0]), reverse = True))

	# Сохранение определений.
	with open("#Definitions.json", "w", encoding = "utf-8") as FileWrite:
		json.dump(TitlesDefinitions, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))
		# Запись в лог сообщения об обновлении файла определений.
		if Answer["new-definitions-count"] > 0:
			logging.info("Definitions file was updated.")

	# Если указано, выдержать интервал перелистывания.
	if Delay == True:
		sleep(Settings["delay"])

	return Answer

# Получение списка слайдов главы и запись в файл.
def GetChapterSlides(Browser, Settings: dict, ChapterID: str, InFuncMessage: str, FroceMode: bool = False):
	# Ссылка на главу.
	ChapterURL = ""
	# Состояние: использован ли режим перезаписи.
	IsForcedModeUsing = True

	# Генерация ссылки на главу.
	try:
		ChapterURL = BuildChapterLinkFromDefinition(Settings, ChapterID)
	# Обработка исключения: ошибка чтения JSON.
	except json.JSONDecodeError:
		# Запись в лог сообщения о провале чтения файла.
		logging.error("Unable to decode JSON file of chapter with ID: " + ChapterID + ".")
	# Обработка исключения: файл не найден.
	except FileNotFoundError:
		# Запись в лог сообщения об отсутствующем файле.
		logging.error("Unable to read \"#Definitions.json\".")
	# Обработка исключения: нет записи в определениях.
	except KeyError:
		# Запись в лог сообщения об отсутствующей записи определения.
		logging.warning("Couldn't find definition for chapter with ID: " + ChapterID + ". Skipped.")

	# Проверка условий перезаписи файла.
	if os.path.exists("chapters/" + ChapterID + ".json") == True and FroceMode == True:
		IsForcedModeUsing = True
	elif os.path.exists("chapters/" + ChapterID + ".json") == True and FroceMode == False:
		IsForcedModeUsing = False

	# Если инструкции перезаписи валидны и URL главы сформирован, то получить слайды.
	if IsForcedModeUsing == True and ChapterURL != "":
		# Переход на страницу чтения главы.
		Browser.get("https://hentaichan.live/online/" + ChapterURL)
		# HTML-код страницы после полной загрузки.
		BodyHTML = Browser.execute_script("return document.body.innerHTML;")
		# Парсинг HTML-кода страницы.
		Soup = BeautifulSoup(BodyHTML, "lxml")
		# Поиск блока со слайдами.
		SlidesBlock = Soup.find("div", {"id": "thumbs"})
		# Парсинг блока со слайдами.
		Soup = BeautifulSoup(str(SlidesBlock), "lxml")
		# Подсчёт количества ссылок на главы.
		SlidesCount = len(Soup.find_all("a"))
		# Получение информации о слайдах главы и сохранение в файл.
		GetSlides(Browser, Settings, ChapterURL, SlidesCount, InFuncMessage)

# Запуск теста Chrome Headless Detection.
def ChromeHeadlessTest(Browser):
	# Переход на стрицу теста.
	Browser.get("https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html")
	# Цветной вывод.
	ColoredPrinterObj = ColoredPrinter()
	# HTML-код страницы после полной загрузки.
	BodyHTML = Browser.execute_script("return document.body.innerHTML;")
	# Парсинг HTML-кода страницы.
	Soup = BeautifulSoup(BodyHTML, "lxml")
	# Получение значения WebDriver.
	UserAgent = RemoveHTML(Soup.find("td", {"id": "user-agent-result"}))
	# Получение значения WebDriver.
	WebDriver = RemoveHTML(Soup.find("td", {"id": "webdriver-result"}))
	# Получение значения Chrome.
	Chrome = RemoveHTML(Soup.find("td", {"id": "chrome-result"}))
	# Получение значения Chrome.
	Permissions = RemoveHTML(Soup.find("td", {"id": "permissions-result"}))
	# Получение значения Chrome.
	PluginsLength = RemoveHTML(Soup.find("td", {"id": "plugins-length-result"}))
	# Получение значения Chrome.
	Languages = RemoveHTML(Soup.find("td", {"id": "languages-result"}))

	# Очистка консоли.
	Cls()
	# Вывод результатов теста.
	print(f"UserAgent: {UserAgent}")
	print("WebDriver: ", end = "")
	if WebDriver == "missing (passed)":
		ColoredPrinterObj.Print(f"{WebDriver}", ColoredPrinterObj.GREEN)
	else:
		ColoredPrinterObj.Print(f"{WebDriver}", ColoredPrinterObj.RED)
	print(f"Chrome: {Chrome}")
	print(f"Permissions: {Permissions}")
	print(f"PluginsLength: {PluginsLength}")
	print(f"Languages: {Languages}\n")
	# Закрытие браузера.
	Browser.close()

	# Пауза.
	input("Press ENTER to exit...")