#!/usr/bin/python

from dublib.Methods import Cls, Shutdown, WriteJSON, ReadJSON
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from Source.Functions import SecondsToTimeString
from Source.TitleParser import TitleParser
from Source.Formatter import Formatter
from Source.Updater import Updater
from dublib.Terminalyzer import *
from selenium import webdriver

import datetime
import logging
import json
import time
import sys
import os

#==========================================================================================#
# >>>>> ПРОВЕРКА ВЕРСИИ PYTHON <<<<< #
#==========================================================================================#

# Минимальная требуемая версия Python.
PythonMinimalVersion = (3, 10)
# Проверка соответствия.
if sys.version_info < PythonMinimalVersion:
	sys.exit("Python %s.%s or later is required.\n" % PythonMinimalVersion)

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ ЛОГГИРОВАНИЯ <<<<< #
#==========================================================================================#

# Если нет папки для логов, то создать.
if os.path.isdir("Logs") == False:
	os.makedirs("Logs")

# Получение текущей даты.
CurrentDate = datetime.datetime.now()
# Время запуска скрипта.
StartTime = time.time()
# Формирование пути к файлу лога.
LogFilename = "Logs/" + str(CurrentDate)[:-7] + ".log"
LogFilename = LogFilename.replace(':', '-')
# Установка конфигнурации.
logging.basicConfig(filename = LogFilename, encoding = "utf-8", level = logging.INFO)
# Отключение части сообщений логов библиотеки requests.
logging.getLogger("requests").setLevel(logging.CRITICAL)

#==========================================================================================#
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#

# Запись в лог сообщения: заголовок подготовки скрипта к работе.
logging.info("====== Preparing to starting ======")
# Запись в лог используемой версии Python.
logging.info("Starting with Python " + str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro) + " on " + str(sys.platform) + ".")
# Запись времени начала работы скрипта.
logging.info("Script started at " + str(CurrentDate)[:-7] + ".")
# Запись команды, использовавшейся для запуска скрипта.
logging.info("Launch command: \"" + " ".join(sys.argv[1:len(sys.argv)]) + "\".")
# Расположении папки установки веб-драйвера в директории скрипта.
os.environ["WDM_LOCAL"] = "1"
# Отключение логов WebDriver.
os.environ["WDM_LOG"] = str(logging.NOTSET)

# Проверка доступности файла настроек.
if os.path.exists("Settings.json"):

	# Открытие файла настроек.
	with open("Settings.json", encoding = "utf-8") as FileRead:
		# Чтение настроек.
		Settings = json.load(FileRead)
		# Запись в лог сообщения об успешном чтении файла настроек.
		logging.info("Settings file was found.")

		# Интерпретация выходной директории обложек и коррекция пути.
		if Settings["covers-directory"] == "":
			Settings["covers-directory"] = "Covers/"
		elif Settings["covers-directory"][-1] != '/':
			Settings["covers-directory"] += "/"

		# Интерпретация выходной директории обложек и коррекция пути.
		if Settings["titles-directory"] == "":
			Settings["titles-directory"] = "Titles/"
		elif Settings["titles-directory"][-1] != '/':
			Settings["titles-directory"] += "/"

		# Приведение формата описательного файла к нижнему регистру.
		Settings["format"] = Settings["format"].lower()

		# Запись в лог сообщения: формат выходного файла.
		logging.info("Output file format: \"" + Settings["format"] + "\".")

		# Запись в лог сообщения: использование ID вместо алиаса.
		if Settings["use-id-instead-slug"] == True:
			logging.info("Using ID instead slug: ON.")
		else:
			logging.info("Using ID instead slug: OFF.")

		# Запись в лог сообщения: использование ID вместо алиаса.
		if Settings["auto-branches-merging"] == True:
			logging.info("Automatic merging of branches: ON.")
		else:
			logging.info("Automatic merging of branches: OFF.")

else:
	# Запись в лог критической ошибки: не найден файл настроек.
	logging.critical("Settings.json not found.")
	# Выброс исключения.
	raise Exception("Settings.json not found")

#==========================================================================================#
# >>>>> НАСТРОЙКА ОБРАБОТЧИКА КОМАНД <<<<< #
#==========================================================================================#

# Список описаний обрабатываемых команд.
CommandsList = list()

# Создание команды: convert.
COM_convert = Command("convert")
COM_convert.addArgument(ArgumentType.All, Important = True)
COM_convert.addArgument(ArgumentType.All, Important = True, LayoutIndex = 1)
COM_convert.addArgument(ArgumentType.All, Important = True)
COM_convert.addFlagPosition(["auto"], Important = True, LayoutIndex = 1)
COM_convert.addFlagPosition(["s"])
CommandsList.append(COM_convert)

# Создание команды: getcov.
COM_getcov = Command("getcov")
COM_getcov.addArgument(ArgumentType.All, Important = True)
COM_getcov.addFlagPosition(["f"])
COM_getcov.addFlagPosition(["s"])
CommandsList.append(COM_getcov)

# Создание команды: parce.
COM_parce = Command("parce")
COM_parce.addArgument(ArgumentType.All, Important = True)
COM_parce.addFlagPosition(["f"])
COM_parce.addFlagPosition(["s"])
CommandsList.append(COM_parce)

# Создание команды: update.
COM_update = Command("update")
COM_update.addArgument(ArgumentType.All, LayoutIndex = 1)
COM_update.addFlagPosition(["local"], LayoutIndex = 1)
COM_update.addFlagPosition(["f"])
COM_update.addFlagPosition(["s"])
COM_update.addKeyPosition(["from"], ArgumentType.All)
CommandsList.append(COM_update)

# Инициализация обработчика консольных аргументов.
CAC = Terminalyzer()
# Получение информации о проверке команд.
CommandDataStruct = CAC.checkCommands(CommandsList)

# Если не удалось определить команду.
if CommandDataStruct == None:
	# Запись в лог критической ошибки: неверная команда.
	logging.critical("Unknown command.")
	# Завершение работы скрипта с кодом ошибки.
	exit(1)

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
if "f" in CommandDataStruct.Flags and CommandDataStruct.Name not in ["convert", "manage"]:
	# Включение режима перезаписи.
	IsForceModeActivated = True
	# Запись в лог сообщения: включён режим перезаписи.
	logging.info("Force mode: ON.")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: ON\n"

else:
	# Запись в лог сообщения об отключённом режиме перезаписи.
	logging.info("Force mode: OFF.")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: OFF\n"

# Обработка флага: выключение ПК после завершения работы скрипта.
if "s" in CommandDataStruct.Flags:
	# Включение режима.
	IsShutdowAfterEnd = True
	# Запись в лог сообщения о том, что ПК будет выключен после завершения работы.
	logging.info("Computer will be turned off after the parser is finished!")
	# Установка сообщения для внутренних функций.
	InFuncMessage_Shutdown = "Computer will be turned off after the parser is finished!\n"

#==========================================================================================#
# >>>>> ОТКРЫТИЕ БРАУЗЕРА <<<<< #
#==========================================================================================#

# Экземпляр веб-драйвера Google Chrome.
Browser = None

# Если потребуется браузер.
if CommandDataStruct.Name in ["getcov", "parce", "update"]:
	# Опции веб-драйвера.
	ChromeOptions = Options()
	# Установка опций.
	ChromeOptions.add_argument("--no-sandbox")
	ChromeOptions.add_argument("--disable-dev-shm-usage")
	ChromeOptions.add_argument("--disable-gpu");
	ChromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])

	# При отключённом режиме отладки скрыть окно браузера.
	if Settings["debug"] is False:
		ChromeOptions.add_argument("--headless=new")

	try:
		# Инициализация браузера.
		Browser = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = ChromeOptions)
		# Установка размера окна браузера на FullHD для корректной работы сайтов.
		Browser.set_window_size(1920, 1080)

	except FileNotFoundError:
		# Запись в лог критической ошибки: неверный путь к вдрайверу.
		logging.critical("Unable to locate webdriver! Try to remove \".wdm\" folder in script directory.")

#==========================================================================================#
# >>>>> ОБРАБОТКА КОММАНД <<<<< #
#==========================================================================================#



# Обработка команды: convert.
if "convert" == CommandDataStruct.Name:
	# Запись в лог сообщения: конвертирование.
	logging.info("====== Converting ======")
	# Структура тайтла.
	Title = None
	# Исходный формат.
	SourceFormat = None
	# Название конвертируемого файла.
	Filename = CommandDataStruct.Arguments[0]
	
	# Добавление расширения к файлу в случае отсутствия такового.
	if ".json" not in Filename:
		Filename += ".json"

	# Чтение тайтла.
	Title = ReadJSON(Settings["titles-directory"] + Filename)

	# Определение исходного формата.
	if "auto" in CommandDataStruct.Flags:
		SourceFormat = Title["format"]
	else:
		SourceFormat = CommandDataStruct.Arguments[1]

	# Создание объекта форматирования.
	FormatterObject = Formatter(Settings, Title, Format = SourceFormat)
	# Конвертирование структуры тайтла.
	Title = FormatterObject.convert(CommandDataStruct.Arguments[2])

	# Сохранение переформатированного описательного файла.
	WriteJSON(Settings["titles-directory"] + Filename, Title)

# Обработка команды: getcov.
if "getcov" == CommandDataStruct.Name:
	# Запись в лог сообщения: заголовок парсинга.
	logging.info("====== Parcing ======")
	# Парсинг тайтла.
	LocalTitle = TitleParser(Settings, Browser, CommandDataStruct.Arguments[0], ForceMode = IsForceModeActivated, Message = InFuncMessage_Shutdown + InFuncMessage_ForceMode, Amending = False)
	# Сохранение локальных файлов тайтла.
	LocalTitle.downloadCover()

# Обработка команды: parce.
if "parce" == CommandDataStruct.Name:
	# Запись в лог сообщения: заголовок парсинга.
	logging.info("====== Parcing ======")
	# Парсинг тайтла.
	LocalTitle = TitleParser(Settings, Browser, CommandDataStruct.Arguments[0], ForceMode = IsForceModeActivated, Message = InFuncMessage_Shutdown + InFuncMessage_ForceMode)
	# Загружает обложку тайтла.
	LocalTitle.downloadCover()
	# Сохранение локальных файлов тайтла.
	LocalTitle.save()

# Обработка команды: update.
if "update" == CommandDataStruct.Name:
	# Запись в лог сообщения: заголовок обновления.
	logging.info("====== Updating ======")
	# Алиас стартового тайтла.
	FromTitle = None
		
	# Если указано, с какого тайтла начать.
	if "from" in CommandDataStruct.Keys:
		FromTitle = CommandDataStruct.Values["from"]

	# Обновить все локальные файлы.
	if "local" in CommandDataStruct.Flags:

		try:
			# Получение списка файлов в директории.
			TitlesList = os.listdir(Settings["titles-directory"])

		except FileNotFoundError:
			TitlesList = list()

		# Фильтрация только файлов формата JSON.
		TitlesList = list(filter(lambda x: x.endswith(".json"), TitlesList))
		# Индекс обрабатываемого тайтла.
		CurrentTitleIndex = 0
		# Алиасы тайтлов.
		TitlesSlugs = list()
			
		# Чтение всех алиасов из локальных файлов.
		for File in TitlesList:
			# Открытие локального описательного файла JSON.
			with open(Settings["titles-directory"] + File, encoding = "utf-8") as FileRead:
				# JSON файл тайтла.
				LocalTitle = json.load(FileRead)

				# Помещение алиаса в список из формата DMP-V1.
				if LocalTitle["format"] == "dmp-v1":
					TitlesSlugs.append(LocalTitle["slug"])

				# Помещение алиаса в список из формата HCMP-V1.
				if LocalTitle["format"] == "hcmp-v1":
					TitlesSlugs.append(str(LocalTitle["id"]) + "-" + LocalTitle["slug"])

		# Запись в лог сообщения: количество доступных для обновления тайтлов.
		logging.info("Local titles to update: " + str(len(TitlesList)) + ".")

		# Старт с указанного тайтла.
		if FromTitle != None:
			# Запись в лог сообщения: стартовый тайтл обновления.
			logging.info("Updating starts from title with slug: \"" + FromTitle + "\".")
			# Буферный список тайтлов.
			BuferTitleSlugs = list()
			# Состояние: записывать ли тайтлы.
			IsWriteSlugs = False
				
			# Перебор тайтлов.
			for Slug in TitlesSlugs:
					
				# Если обнаружен стартовый тайтл, то включить запись тайтлов в новый список обновлений.
				if Slug == FromTitle:
					IsWriteSlugs = True
						
				# Добавить алиас в список обновляемых тайтлов.
				if IsWriteSlugs is True:
					BuferTitleSlugs.append(Slug)

			# Перезапись списка обновляемых тайтлов.
			TitlesSlugs = BuferTitleSlugs
				
		# Запись в лог сообщения: заголовок парсинга.
		logging.info("====== Parcing ======")

		# Парсинг обновлённых тайтлов.
		for Slug in TitlesSlugs:
			# Инкремент текущего индекса.
			CurrentTitleIndex += 1
			# Очистка терминала.
			Cls()
			# Вывод в терминал прогресса.
			print("Updating titles: " + str(len(TitlesList) - len(TitlesSlugs) + CurrentTitleIndex) + " / " + str(len(TitlesList)))
			# Генерация сообщения.
			ExternalMessage = InFuncMessage_Shutdown + InFuncMessage_ForceMode + "Updating titles: " + str(len(TitlesList) - len(TitlesSlugs) + CurrentTitleIndex) + " / " + str(len(TitlesList)) + "\n"
			# Парсинг тайтла.
			LocalTitle = TitleParser(Settings, Browser, Slug.replace(".json", ""), ForceMode = IsForceModeActivated, Message = ExternalMessage)
			# Загрузка обложек.
			LocalTitle.downloadCover()
			# Сохранение локальных файлов тайтла.
			LocalTitle.save()

	# Обновить изменённые на сервере за последнее время тайтлы.
	else:
		# Инициализация проверки обновлений.
		UpdateChecker = Updater(Settings, Browser)
		# Получение списка обновлённых тайтлов.
		UpdatedTitlesList = UpdateChecker.GetUpdatesList()
		# Индекс обрабатываемого тайтла.
		CurrentTitleIndex = 0
		# Запись в лог сообщения: количество найденных за указанный период обновлений.
		logging.info("Titles found for update period: " + str(len(UpdatedTitlesList)) + ".")

		# Старт с указанного тайтла.
		if FromTitle != None:
			# Запись в лог сообщения: стартовый тайтл обновления.
			logging.info("Updating starts from title with slug: \"" + FromTitle + "\".")
			# Буферный список тайтлов.
			BuferTitleSlugs = list()
			# Состояние: записывать ли тайтлы.
			IsWriteSlugs = False
				
			# Перебор тайтлов.
			for Slug in UpdatedTitlesList:
					
				# Если обнаружен стартовый тайтл, то включить запись тайтлов в новый список обновлений.
				if Slug == FromTitle:
					IsWriteSlugs = True
						
				# Добавить алиас в список обновляемых тайтлов.
				if IsWriteSlugs is True:
					BuferTitleSlugs.append(Slug)

			# Перезапись списка обновляемых тайтлов.
			UpdatedTitlesList = BuferTitleSlugs

		# Запись в лог сообщения: заголовог парсинга.
		logging.info("====== Parcing ======")

		# Парсинг обновлённых тайтлов.
		for Slug in UpdatedTitlesList:
			# Инкремент текущего индекса.
			CurrentTitleIndex += 1
			# Генерация сообщения.
			ExternalMessage = InFuncMessage_Shutdown + InFuncMessage_ForceMode + "Updating titles: " + str(CurrentTitleIndex) + " / " + str(len(UpdatedTitlesList)) + "\n"
			# Парсинг тайтла.
			LocalTitle = TitleParser(Settings, Browser, Slug, ForceMode = IsForceModeActivated, Message = ExternalMessage)
			# Загрузка обложек.
			LocalTitle.downloadCover()
			# Сохранение локальных файлов тайтла.
			LocalTitle.save()

#==========================================================================================#
# >>>>> ЗАВЕРШЕНИЕ РАБОТЫ СКРИПТА <<<<< #
#==========================================================================================#

try:
	# Попытка закрыть браузер.
	Browser.close()

except Exception:
	pass

# Запись в лог сообщения: заголовок завершения работы скрипта.
logging.info("====== Exiting ======")
# Очистка консоли.
Cls()
# Время завершения работы скрипта.
EndTime = time.time()
# Запись времени завершения работы скрипта.
logging.info("Script finished at " + str(datetime.datetime.now())[:-7] + ". Execution time: " + SecondsToTimeString(EndTime - StartTime) + ".")

# Выключение ПК, если установлен соответствующий флаг.
if IsShutdowAfterEnd == True:
	# Запись в лог сообщения о немедленном выключении ПК.
	logging.info("Turning off the computer.")
	# Выключение ПК.
	Shutdown()

# Выключение логгирования.
logging.shutdown()