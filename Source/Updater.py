from Source.BrowserNavigator import BrowserNavigator
from selenium import webdriver
from bs4 import BeautifulSoup

import datetime
import logging
import json

class Updater:
    
    #==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Текущая дата.
	__CurrentDate = datetime.datetime.now()
	# Глобальные настройки.
	__Settings = dict()
	# Обработчик навигации экземпляра браузера.
	__Navigator = None

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Возвращает количество дней, прошедших с момента публикации.
	def __GetElapsedDays(self, Date: str) -> int:
		# Дата публикации
		ChapterPublicationDate = datetime.datetime.strptime(Date, "%d %m %Y")
		# Прошедшее с момента публикации время.
		Duration = self.__CurrentDate - ChapterPublicationDate
		# Количество дней, прошедших с момента публикации.
		DurationInDays  = Duration.days

		return DurationInDays

	# Возвращает дату публикации главы.
	def __GetPublicationDate(self, Block: str) -> str:
		# Парсинг HTML блока главы.
		Soup = BeautifulSoup(Block, "lxml")


	# Конструктор: задаёт глобальные настройки и инициализирует объект.
	def __init__(self, Settings: dict, Browser: webdriver.Chrome):

		#---> Генерация свойств.
		#==========================================================================================#
		self.__Settings = Settings
		self.__Navigator = BrowserNavigator(Settings, Browser)

	# Возвращает список алиасов обновлённых тайтлов.
	def GetUpdatesList(self) -> list:
		# Список алиасов обновлённых тайтлов.
		Updates = list()
		# Индекс текущей страницы.
		PageIndex = 0
		# Состояние: получены ли все обновления.
		IsAllUpdatesRecieved = False
		# Список блоков обновлённых глав.
		UpdatedChaptersBlocks = list()

		# Загружать страницы каталога последовательно.
		while IsAllUpdatesRecieved == False:
			# Переход на страницу каталога.
			self.__Navigator.LoadPage("https://hentaichan.live/manga/new?offset=" + str(20 * PageIndex))
			# HTML код тела страницы после полной загрузки.
			BodyHTML = self.__Navigator.GetBodyHTML()
			# Парсинг HTML кода страницы.
			Soup = BeautifulSoup(BodyHTML, "lxml")
			# Поиск всех блоков глав.
			ChaptersBlocks = Soup.find_all("div", {"class": "content_row"})

			# Проверка блоков на соответствие временным рамкам.
			for Block in ChaptersBlocks:
				pass


		return Updates