from dublib.WebRequestor import WebRequestor
from dublib.Methods import Cls
from bs4 import BeautifulSoup

import datetime

class Updater:

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
	def __init__(self, Settings: dict, Navigator: WebRequestor):

		#---> Генерация свойств.
		#==========================================================================================#
		# Текущая дата.
		self.__CurrentDate = datetime.datetime.now()
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Обработчик навигации экземпляра браузера.
		self.__Navigator = Navigator

	# Возвращает список алиасов обновлённых тайтлов.
	def getUpdatesList(self) -> list:
		# Список алиасов обновлённых тайтлов.
		Updates = list()
		# Индекс текущей страницы.
		PageIndex = 0
		# Состояние: получены ли все обновления.
		IsAllUpdatesRecieved = False
		
		# Загружать страницы каталога последовательно.
		while IsAllUpdatesRecieved == False:
			# Список блоков новых глав, соответствующих заданному периоду.
			UpdatedChaptersBlocks = list()
			# Очистка консоли.
			Cls()
			# Вывод в консоль: сканируемая страница.
			print("Scanning page: " + str(PageIndex + 1))
			# Запрос страницы каталога.
			Response = self.__Navigator.get("https://hentaichan.live/manga/newest?offset=" + str(20 * PageIndex))
			# Парсинг HTML кода страницы.
			Soup = BeautifulSoup(Response.text, "html.parser")
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
					
			# Если достигнута последняя страница.
			if len(ChaptersBlocks) == 0:
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