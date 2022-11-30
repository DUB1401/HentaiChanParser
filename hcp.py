#!/usr/bin/env python3.9

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome
from PIL import ImageFile
from time import sleep

import datetime
import logging
import json
import time
import sys
import os

from BaseFunctions import GetLastChapterDefinitionID
from BaseFunctions import SecondsToTimeString
from BaseFunctions import GetPagesCount
from BaseFunctions import Shutdown
from BaseFunctions import LogIn
from BaseFunctions import Cls

from Components import ChromeHeadlessTest
from Components import GetChapterSlides
from Components import ScanTitles

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ ЛОГОВ <<<<< #
#==========================================================================================#

# Получение текущей даты.
CurrentDate = datetime.datetime.now()
# Время запуска скрипта.
StartTime = time.time()
# Формирование пути к файлу лога.
LogFilename = "Logs\\" + str(CurrentDate)[:-7] + ".log"
LogFilename = LogFilename.replace(':', '-')
# Установка конфигнурации.
logging.basicConfig(filename = LogFilename, encoding = "utf-8", level = logging.INFO)

#==========================================================================================#
# >>>>> ОТКРЫТИЕ БРАУЗЕРА <<<<< #
#==========================================================================================#

# Расположении папки установки веб-драйвера в директории скрипта.
os.environ["WDM_LOCAL"] = "1"
# Разрешить чтение усечённых файлов.
ImageFile.LOAD_TRUNCATED_IMAGES = True
# Установка параметров работы браузера: отключение вывода логов в консоль, отключение аппаратного ускорения.
BrowserOptions = Options()
BrowserOptions.add_argument("--log-level=3")
BrowserOptions.add_argument("--disable-gpu")
BrowserOptions.add_argument("--disable-blink-features=AutomationControlled")
# Загрузка веб-драйвера и установка его в качестве используемого модуля.
Browser = Chrome(service = Service(ChromeDriverManager().install()), options = BrowserOptions)
# Очистка куков перед запуском (предположительный фикс бага авторизации).
Browser.delete_all_cookies()
# Очистка консоли от данных о сессии.
Cls()
# Установка размера окна браузера на FullHD для корректной работы сайтов.
Browser.set_window_size(1920, 1080)

#==========================================================================================#
# >>>>> ПРОВЕРКА НАЛИЧИЯ ДИРЕКТОРИЙ <<<<< #
#==========================================================================================#

# Список необходимых директорий.
ImportantDirectories = ["hentai", "chapters"]

# Создание отсутствующих директорий.
for DirectoryName in ImportantDirectories:
	if os.path.isdir(DirectoryName) == False:
		os.makedirs(DirectoryName)

#==========================================================================================#
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#

# Вывод в лог заголовка: подготовка скрипта к работе.
logging.info("====== Prepare to starting ======")
# Запись времени начала работы скрипта.
logging.info("Script started at " + str(CurrentDate)[:-7] + ".")
# Запись команды, использовавшейся для запуска скрипта.
logging.info("Launch command: \"" + " ".join(sys.argv[1:len(sys.argv)]) + "\".")
# Инициализация хранилища настроек со стадартными значениями.
Settings = {
    "directory" : "",
    "scan-target" : "",
	"login": "",
    "password": "",
    "delay": 5,
    "getting-slide-sizes": False,
    "logs-cleanup": True,
	"last-scan-new-range": ""
}

# Открытие файла настроек.
try:
	with open("Settings.json") as FileRead:
		Settings = json.load(FileRead)
		# Проверка успешной загрузки файла.
		if Settings == None:
			# Запись в лог ошибки о невозможности прочитать битый файл.
			logging.error("Unable to read \"Settings.json\". File is broken.")
		else:
			# Запись в лог сообщения об успешном чтении файла настроек.
			logging.info("The settings file was found successfully.")

			# Если директория загрузки не установлена, задать значение по умолчанию.
			if Settings["directory"] == "":
				# Установка директории по умолчанию на основе домена.
				Settings["directory"] = "hentai"
				# Запись в лог сообщения об установке стандартной директории загрузки.
				logging.info("Save directory set as default.")
			else:
				# Запись в лог сообщения об установке директории загрузки.
				logging.info("Save directory set as " + Settings["directory"] + ".")

			# Если директория не существует, тогда создать её.
			if os.path.exists(Settings["directory"]) == False:
					os.makedirs(Settings["directory"])

			# Вывести сообщение об отключеннии получения размеров слайдов.
			if Settings["getting-slide-sizes"] == False:
				logging.info("Images sizing is disabled.")
# Обработка исключений: любое исключение.
except EnvironmentError:
	# Запись в лог ошибки о невозможности открытия файла настроек.
	logging.error("Unable to open \"Settings.json\". All options set as default.")

#==========================================================================================#
# >>>>> ОБРАБОТКА СПЕЦИАЛЬНЫХ ФЛАГОВ <<<<< #
#==========================================================================================#

# Активна ли опция выключения компьютера по завершении работы парсера.
IsShutdowAfterEnd = False
# Сообщение для внутренних функций: выключение ПК.
InFuncMessage_Shutdown = ""
# Активен ли режим перезаписи при парсинге.
IsForceModeActivated = False
# Сообщение для внутренних функций: режим перезаписи.
InFuncMessage_ForceMode = ""

# Обработка флага: режим перезаписи.
if "-f" in sys.argv:
	# Включение режима перезаписи.
	IsForceModeActivated = True
	# Запись в лог сообщения о включении режима перезаписи.
	logging.info("Force mode: ON")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: ON\n"
else:
	# Запись в лог сообщения об отключённом режиме перезаписи.
	logging.info("Force mode: OFF")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: OFF\n"

# Обработка флага: выключение ПК после завершения работы скрипта.
if "-s" in sys.argv:
	# Включение режима.
	IsShutdowAfterEnd = True
	# Запись в лог сообщения о том, что ПК будет выключен после завершения работы.
	logging.info("Computer will be turned off after the parser is finished!")
	# Установка сообщения для внутренних функций.
	InFuncMessage_Shutdown = "Computer will be turned off after the parser is finished!\n"

#==========================================================================================#
# >>>>> ОБРАБОТКА ОСНОВНЫХ КОММАНД <<<<< #
#==========================================================================================#

# Двухкомпонентные команды: parce, update, scan.
if len(sys.argv) >= 3:
	# Вход на сайт.
	LogIn(Browser, Settings)

	# Сканирование обновлений на сайте и их запись.
	if sys.argv[1] == "scan":
		# Вывод в лог заголовка: другие методы.
		logging.info("====== Scanning ======")
		# Количество добавленных определений.
		NewDefinitionsCount = 0

		# Сканирование главы с переданным ID.
		if sys.argv[2].isdigit() == True:
			# Запись в лог сообщение о начале сканирования страницы.
			logging.info("Scanning site on page: " + sys.argv[2] + "...")
			# Сканирование страницы.
			Answer = ScanTitles(Browser, Settings, sys.argv[2], "Scanning site on page: " + sys.argv[2])
			# Подсчёт новых определений.
			NewDefinitionsCount += Answer["new-definitions-count"]

		# Сканирование всего сайта.
		if sys.argv[2] == "-all":
			# Запись в лог сообщение о начале сканирования всего сайта.
			logging.info("Scanning all site...")
			# Количество страниц на сайте.
			PagesCount = int(GetPagesCount(Browser, Settings))

			# Сканировать каждую страницу.
			for PageNumber in range(1, PagesCount):
				# Формирование строки внутрифункционального вывода.
				InFuncMessage = InFuncMessage_Shutdown + "Scanning site on page: " + str(PageNumber) + " / " + str(PagesCount)
				# Сканирование страницы.
				Answer = ScanTitles(Browser, Settings, PageNumber, InFuncMessage, Delay = True)
				# Подсчёт новых определений.
				NewDefinitionsCount += Answer["new-definitions-count"]

		# Сканирование обновлений сайта.
		if sys.argv[2] == "-new":
			# Запись в лог сообщение о начале сканирования обновлений сайта.
			logging.info("Scanning updates on site...")
			# Количество страниц на сайте.
			PagesCount = int(GetPagesCount(Browser)) + 1
			# Последний ID определения до сканирования.
			LastChapterIDBeforeScanning = GetLastChapterDefinitionID()
			# Последний ID определения после сканирования.
			LastChapterIDAfterScanning = ""

			# Сканировать каждую страницу.
			for PageNumber in range(1, PagesCount):
				# Формирование строки внутрифункционального вывода.
				InFuncMessage= InFuncMessage_Shutdown + "Scanning updates on page: " + str(PageNumber)
				# Сканирование страницы.
				Answer = ScanTitles(Browser, Settings, PageNumber, InFuncMessage, Delay = True)
				# Подсчёт новых определений.
				NewDefinitionsCount += Answer["new-definitions-count"]
				# Если функция сканирования нашла совпадение по ID главы, то завершить сканирование.
				if Answer["already-exists"] == True:
					break

			# Запись в лог сообщения о завершении сканирования.
			logging.info("Completed. New definitions count: " + str(NewDefinitionsCount) + ".")
			# Получение последнего ID определения после сканирования.
			LastChapterIDAfterScanning = GetLastChapterDefinitionID()

			# Если сформирован диапазон последнего обновления, то сохранить его.
			if LastChapterIDBeforeScanning != "" and LastChapterIDBeforeScanning != LastChapterIDAfterScanning:
				# Формирование текстового диапазона.
				Settings["last-scan-new-range"] = LastChapterIDBeforeScanning + '-' + LastChapterIDAfterScanning

				# Сохранение настроек.
				with open("Settings.json", "w", encoding = "utf-8") as FileWrite:
					json.dump(Settings, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))

	# Получение слайдов одной главы и сохранение в файл.
	if sys.argv[1] == "getsl":
		# Вывод в лог заголовка: другие методы.
		logging.info("====== Parcing ======")

		# Получение слайдов главы с переданным ID.
		if sys.argv[2].isdigit() == True:
			# Генерирование сообщения для внутренних функций.
			InFuncMessage = InFuncMessage_Shutdown + InFuncMessage_ForceMode
			# Запуск процесса.
			GetChapterSlides(Browser, Settings, sys.argv[2], InFuncMessage, FroceMode = IsForceModeActivated)

# Однокомпонентные команды: chtest.
if len(sys.argv) >= 2:

	# Тестирование парсера на скрытность.
	if sys.argv[1] == "chtest":
		# Вывод в лог заголовка: другие методы.
		logging.info("====== Other ======")
		# Запуск теста Chrome Headless Detection.
		ChromeHeadlessTest(Browser)

# Обработка исключения: недостаточно аргументов.
elif len(sys.argv) == 1:
	logging.error("Not enough arguments.")

#==========================================================================================#
# >>>>> ЗАВЕРШЕНИЕ РАБОТЫ СКРИПТА <<<<< #
#==========================================================================================#

# Вывод в лог заголовка: завершение работы.
logging.info("====== Exiting ======")

# Закрытие браузера, если уже не закрыт.
try:
	Browser.close()
# Обработка исключения: любое исключение.
except Exception:
	pass

# Очистка консоли.
Cls()

# Время завершения работы скрипта.
EndTime = time.time()
# Запись времени завершения работы скрипта.
logging.info("Script finished at " + str(datetime.datetime.now())[:-7] + ". Execution time: " + SecondsToTimeString(EndTime - StartTime) + ".")
# Выключение логгирования.
logging.shutdown()

# Удаление лога, если в процессе работы скрипта не проводился парсинг или обновление, а также указано настройками.
if "parce" not in sys.argv and "update" not in sys.argv and Settings["logs-cleanup"] == True:
	os.remove(LogFilename)

# Выключение ПК, если установлен соответствующий флаг.
if IsShutdowAfterEnd == True:
	# Запись в лог сообщения о немедленном выключении ПК.
	logging.info("Turning off the computer.")
	# Выключение ПК.
	Shutdown()
