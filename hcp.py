#!/usr/bin/python

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from Source.Functions import SecondsToTimeString
from Source.TitleParser import TitleParser
from Source.DUBLIB import Shutdown
from selenium import webdriver
from Source.DUBLIB import Cls

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
PythonMinimalVersion = (3, 9)
# Проверка соответствия.
if sys.version_info < PythonMinimalVersion:
	sys.exit("Python %s.%s or later is required.\n" % PythonMinimalVersion)

#==========================================================================================#
# >>>>> ПРОВЕРКА НАЛИЧИЯ ДИРЕКТОРИЙ <<<<< #
#==========================================================================================#

# Список необходимых директорий.
ImportantDirectories = ["Covers", "Logs", "Titles"]

# Создание отсутствующих директорий.
for DirectoryName in ImportantDirectories:
	if os.path.isdir(DirectoryName) == False:
		os.makedirs(DirectoryName)

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ ЛОГОВ <<<<< #
#==========================================================================================#

# Получение текущей даты.
CurrentDate = datetime.datetime.now()
# Время запуска скрипта.
StartTime = time.time()
# Формирование пути к файлу лога.
LogFilename = "Logs/" + str(CurrentDate)[:-7] + ".log"
LogFilename = LogFilename.replace(':', '-')
# Установка конфигнурации.
logging.basicConfig(filename = LogFilename, encoding = "utf-8", level = logging.INFO)

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
# Глобальные настройки.
Settings = {
	"format": "dmp-v1",
	"sizing-images": False,
	"use-id-instead-slug": False,
	"auto-branches-merging": False,
	"covers-directory": "",
	"titles-directory": "",
	"retry-tries": 3,
	"retry-delay": 15,
	"debug": False
}

# Проверка доступности файла.
if os.path.exists("Settings.json"):

	# Открытие файла настроек.
	with open("Settings.json") as FileRead:
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

		# Запись в шапку лога формата выходного файла.
		logging.info("Output file format: \"" + Settings["format"] + "\".")

#==========================================================================================#
# >>>>> ОТКРЫТИЕ БРАУЗЕРА <<<<< #
#==========================================================================================#

# Экземпляр веб-драйвера Google Chrome.
Browser = None
# Опции веб-драйвера.
ChromeOptions = Options()
# Установка опций.
ChromeOptions.add_argument("--no-sandbox")
ChromeOptions.add_argument("--disable-dev-shm-usage")
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
	logging.critical("Unable to locate webdriver! Try to remove \".wdm\" folder in script directory.")

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

	# Парсинг тайтла.
	if sys.argv[1] == "parce":
		# Запись в лог сообщения: заголовок парсинга.
		logging.info("====== Parcing ======")
		# Парсинг тайтла.
		LocalTitle = TitleParser(Settings, Browser, sys.argv[2])
		# Сохранение локальных файлов тайтла.
		LocalTitle.Save()

# Обработка исключения: недостаточно аргументов.
elif len(sys.argv) == 1:
	logging.error("Not enough arguments.")

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