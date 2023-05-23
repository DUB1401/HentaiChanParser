from Source.BrowserNavigator import BrowserNavigator
from selenium import webdriver
from bs4 import BeautifulSoup

import datetime

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
		# Перевод даты.
		Date = self.__TranclateMouthInDate(Date)
		# Дата публикации
		ChapterPublicationDate = datetime.datetime.strptime(Date, "%d %B %Y")
		# Прошедшее с момента публикации время.
		Duration = self.__CurrentDate - ChapterPublicationDate
		# Количество дней, прошедших с момента публикации.
		DurationInDays  = Duration.days

		return DurationInDays

	# Возвращает дату публикации главы.
	def __GetPublicationDate(self, Block: str) -> str:
		# Парсинг HTML блока главы.
		Soup = BeautifulSoup(str(Block), "html.parser")
		# Поиск блока строки описания с датой.
		RowBlock = Soup.find("div", {"class": "row4_right"})
		# Парсинг блока строки описания с датой.
		Soup = BeautifulSoup(str(RowBlock), "html.parser")
		# Поиск блока с датой.
		DateBlock = Soup.find("b")
		# Получение текстового варианта даты.
		Date = DateBlock.get_text().strip()

		return Date

	# Возвращает дату публикации главы с английской вариацией месяца в именительном падеже.
	def __TranclateMouthInDate(self, Date: str) -> str:
		# Список месяцев на русском в родительном падеже.
		RussianMonths = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
		# Список месяцев на английском в именительном падеже.
		EnglishMonths = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

		# Для каждого месяца.
		for MounthIndex in range(0, 12):

			# Если в дате обнаружен русский месяц, то заменить его на английский вариант.
			if RussianMonths[MounthIndex] in Date:
				Date = Date.replace(RussianMonths[MounthIndex], EnglishMonths[MounthIndex])

		return Date

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
		# Список блоков новых глав, соответствующих заданному периоду.
		UpdatedChaptersBlocks = list()

		# Загружать страницы каталога последовательно.
		while IsAllUpdatesRecieved == False:
			# Переход на страницу каталога.
			self.__Navigator.LoadPage("https://hentaichan.live/manga/new?offset=" + str(20 * PageIndex))
			# HTML код тела страницы после полной загрузки.
			BodyHTML = self.__Navigator.GetBodyHTML()
			# Парсинг HTML кода страницы.
			Soup = BeautifulSoup(BodyHTML, "html.parser")
			# Поиск всех блоков глав.
			ChaptersBlocks = Soup.find_all("div", {"class": "content_row"})
			# Инкремент индекса страницы.
			PageIndex += 1

			# Для каждого блока главы на странице каталога.
			for Block in ChaptersBlocks:
				
				# Если дата загрузки главы соответствует заданному периоду.
				if self.__GetElapsedDays(self.__GetPublicationDate(Block)) < self.__Settings["check-updates-period"]:
					UpdatedChaptersBlocks.append(Block)

				# Если дата загрузки главы вышла за пределы заданного периода.
				else:
					IsAllUpdatesRecieved = True

		# Для каждого блока новой главы, соответствующего заданному периоду.
		for Block in UpdatedChaptersBlocks:
			# Парсинг блока главы.
			Soup = BeautifulSoup(str(Block), "html.parser")
			# Поиск ссылки на тайтл.
			TitleLink = Soup.find("a", {"class": "title_link"})
			# Получение алиаса.
			Slug = TitleLink["href"].replace(".html", "").replace("/manga/", "")
			# Сохранение алиаса.
			Updates.append(Slug)

		return Updates