from Source.BrowserNavigator import BrowserNavigator
from Source.DUBLIB import CheckForCyrillicPresence
from selenium import webdriver
from bs4 import BeautifulSoup

import enchant
import logging
import json
import re

class TitleParser:

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Глобальные настройки.
	__Settings = dict()
	# Обработчик навигации экземпляра браузера.
	__Navigator = None
	# Экземпляр браузера.
	__Browser = None
	# Описательная структура тайтла.
	__Title = None
	# Алиас тайтла.
	__Slug = None
	# ID тайтла.
	__ID = None

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Возвращает список URL глав тайтла.
	def __GetChaptersList(self) -> list:
		# Список URL глав тайтла.
		ChaptersList = list()
		# URL всех глав тайтла или похожих тайтлов.
		TitleURL = "https://hentaichan.live/related/" + self.__Slug + ".html"
		# Переход на страницу всех глав тайтла или похожих тайтлов.
		self.__Navigator.LoadPage(TitleURL)
		# HTML код тела страницы после полной загрузки.
		PageHTML = self.__Navigator.GetPageHTML()
		# Парсинг HTML кода тела страницы.
		Soup = BeautifulSoup(PageHTML, "lxml")
		
		# Если у тайтла одна глава.
		if "Хентай похожий на" in str(PageHTML):
			# Запись URL единственной главы.
			ChaptersList.append(self.__Slug)
			
		# Если у тайтла больше одной главы.
		else:
			# Запись в лог предупреждения: 
			logging.warning("This title isn't single. Not supported.")

	# Возвращает её описательную структуру в формате DMP-V1.
	def __GetCoverData(self, PageHTML: str) -> dict:
		# Контейнер обложек.
		CoversList = list()
		# Парсинг HTML кода тела страницы.
		Soup = BeautifulSoup(PageHTML, "lxml")
		# Поиск HTML элемента обложки.
		CoverHTML = Soup.find("img", {"id": "cover"})
		# Описательная структура обложки.
		Cover = {
			"link": None,
			"filename": None,
			"width": None,
			"height": None
			}

		# Если обложка есть, определить её URL и название.
		if "src" in CoverHTML.attrs.keys():
			Cover["link"] = str(CoverHTML["src"])
			Cover["filename"] = Cover["link"].split('/')[-1]
			CoversList.append(Cover)

		return CoversList

	# Возвращает структуру жанров и тегов в формате DMP-V1.
	def __GetGenresAndTags(self, PageHTML: str) -> dict:
		# Структура жанров и тегов.
		GenresAndTags = {
			"tags": list(),
			"genres": list()
			}
		# Парсинг HTML кода тела страницы.
		Soup = BeautifulSoup(PageHTML, "lxml")
		# Поиск всех HTML элементов тегов.
		AllTags = Soup.find_all("li", {"class": "sidetag"})

		# Для каждого тега сформировать структуру согласно формату DMP-V1.
		for Tag in AllTags:
			# Буферная структура.
			Bufer = {
				"id": None,
				"name": None
				}
			# Запись в буфер названия, очищенного от знаков навигации.
			Bufer["name"] = Tag.get_text().replace("\n", "").replace("+-", "")
			# Добавление буфера в общую структуру.
			GenresAndTags["tags"].append(Bufer)
		
		return GenresAndTags

	# Заполняет информацию о тайтле.
	def __GetTitleData(self):
		# URL тайтла.
		TitleURL = "https://hentaichan.live/manga/" + self.__Slug + ".html"
		# Переход на страницу тайтла.
		self.__Navigator.LoadPage(TitleURL)
		# HTML код тела страницы после полной загрузки.
		PageHTML = self.__Navigator.GetPageHTML()
		# Парсинг HTML кода тела страницы.
		Soup = BeautifulSoup(PageHTML, "lxml")
		# Поиск HTML элемента названия тайтла.
		TitleName = Soup.find("a", {"class": "title_top_a"}).get_text()
		# Структура названия главы: русское, английское и другие.
		ParcedTitleName = self.__ParceTitleName(TitleName)
		# Поиск HTML элемента описания.
		DescriptionHTML = Soup.find("div", {"id": "description"})
		# Описание тайтла.
		Description = None
		# Получение структур жанров и тегов.
		GenresAndTags = self.__GetGenresAndTags(PageHTML)

		# Проверка наличия описания.
		if DescriptionHTML != None:

			# Удаление вложенных блоков из описания.
			for Block in DescriptionHTML.select("div"):
				Block.decompose()

			# Замена тегов на спецсимволы новой строки.
			DescriptionHTML = BeautifulSoup(str(DescriptionHTML).replace("<br/>", "\n"), "lxml")
			# Получение оставшегося текста без краевых спецсимволов и пробелов.
			Description = DescriptionHTML.get_text().strip("\n \t")

			# Если описание пустое, то обнулить его.
			if Description == "":
				Description = None

		# Заполнение полей описательной структуры.
		self.__Title["site"] = "hentaichan.live"
		self.__Title["id"] = int(self.__ID)
		self.__Title["slug"]
		self.__Title["covers"] = self.__GetCoverData(PageHTML)
		self.__Title["ru-name"] = ParcedTitleName["ru-name"]
		self.__Title["en-name"] = ParcedTitleName["en-name"]
		self.__Title["another-names"] = ParcedTitleName["another-names"]
		self.__Title["type"]
		self.__Title["age-rating"] = 18
		self.__Title["publication-year"]
		self.__Title["status"]
		self.__Title["description"] = Description
		self.__Title["is-licensed"]
		self.__Title["genres"] = GenresAndTags["genres"]
		self.__Title["tags"] = GenresAndTags["tags"]

		# Запись в лог сообщения: получено описание тайтла.
		logging.info("Title: \"" + self.__Slug + "\". Request title description... Done.")

	# Возвращает структуру из русского, английского и других названий тайтла.
	def __ParceTitleName(self, TitleName: str) -> dict:
		# Структура названий.
		TitleNameStruct = {
			"ru-name": None,
		    "en-name": None,
		    "another-names": None
			}

		# Список ругулярных выражений для поиска номера главы.
		ChapterNumberReList = [r"глав[аы] \d+([\.-])?(\d+)?", r"\d+([\.-])?(\d+)? глав[аы]", r"част[иь] \d+([\.-])?(\d+)?", r"\d+([\.-])?(\d+)? част[иь]", r"Ch. \d+([\.-])?(\d+)?"]
		# Поиск части названия в скобочках.
		BracketsPart = re.search("(?<=\()(.*?)(?=\))", TitleName, re.IGNORECASE)
		# Части названия.
		NamePartsList = []

		# Если есть часть названия в скобочках.
		if BracketsPart is not None:
			# Преобразование в текст части названия в скобочках.
			BracketsPart = BracketsPart.group(0)
			# Удаление из заголовка части названия в скобочках.
			TitleName = TitleName.replace("(" + BracketsPart + ")", "")
			# Очистка конечных пробельных символов заголовка.
			TitleName = TitleName.strip()
			# Запись названия в скобочках как полноценного.
			NamePartsList.append(BracketsPart)
			# Запись названия без скобочек как полноценного.
			NamePartsList.append(TitleName)

		# Буфер имён после удаления номера главы.
		NameBufer = []

		# Удаление из названий номера главы.
		for Name in NamePartsList:
			for i in range(0, len(ChapterNumberReList)):
				# Буфер поиска.
				Bufer = re.search(ChapterNumberReList[i], Name, re.IGNORECASE)
			
				# Если буфер валиден, то удалить номер главы.
				if Bufer is not None:
					Name = Name.replace(Bufer.group(0), "")
					Name = Name.strip(" -")

			# Сохранение названия без номера главы.
			NameBufer.append(Name)

		# Проверка локализаций названий.
		for Name in NameBufer:
			# Состояние: удалось ли в текущем цикле определить локализацию названия.
			IsLocaled = False

			# Обработка: русское название.
			for Character in Name:
				if CheckForCyrillicPresence(Character) is True:
					TitleNameStruct["ru-name"] = Name
					IsLocaled = True

			# Обработка: английское название.
			if IsLocaled == False:
				# Словарь английских слов.
				DictEnUS = enchant.Dict("en_US")

				# Проверка каждого слова длиннее двух символов по словарю.
				for Word in list(Name.split(' ')):
					if len(Word) > 2 and DictEnUS.check(Word) == True:
						TitleNameStruct["en-name"] = Name
						IsLocaled = True

			# Обработка: транслитерированное название.
			if IsLocaled == False:

				# Преобразование пустого поля других названий.
				if TitleNameStruct["another-names"] == None:
					TitleNameStruct["another-names"] = str()

				# Запись альтернативных названий через запятую.
				TitleNameStruct["another-names"] += Name + " / "

		# Очистка альтернативных названий от ненужных краевых символов.
		if TitleNameStruct["another-names"] != None:
			TitleNameStruct["another-names"] = TitleNameStruct["another-names"].strip(" / ")

		return TitleNameStruct

	# Конструктор: задаёт глоабльные настройки, экземпляр браузера и алиас тайтла. Инициализирует парсер.
	def __init__(self, Settings: dict, Browser: webdriver.Chrome, Slug: str):

		#---> Генерация свойств.
		#==========================================================================================#
		self.__Settings = Settings
		self.__Navigator = BrowserNavigator(Settings, Browser)
		self.__Browser = Browser
		self.__Title = {
			"format": "dmp-v1",
			"site": None,
			"id": None,
			"slug": None,
			"covers": list(),
			"ru-name": None,
			"en-name": None,
			"another-names": None,
			"type": None,
			"age-rating": None,
			"publication-year": None,
			"status": None,
			"description": None,
			"is-licensed": None,
			"genres": list(),
			"tags": list(),
			"branches": list(),
			"chapters": dict()
		}
		self.__Slug = Slug
		self.__ID = Slug.split('-')[0]
		
		#---> Получение данных о тайтле.
		#==========================================================================================#
		# Запись в лог сообщения: парсинг начат.
		logging.info("Title: \"" + self.__Slug + "\". Parcing...")
		# Получение описательных данных тайтла.
		self.__GetTitleData()

	# Сохраняет локальный JSON файл.
	def Save(self):

		# Используемое имя тайтла: ID или алиас.
		UsedTitleName = None

		# Установка используемого имени тайтла.
		if self.__Settings["use-id-instead-slug"] == False:
			UsedTitleName = self.__Slug
		else:
			UsedTitleName = self.__ID

		# Сохранение локального файла JSON.
		with open(self.__Settings["titles-directory"] + UsedTitleName + ".json", "w", encoding = "utf-8") as FileWrite:
			json.dump(self.__Title, FileWrite, ensure_ascii = False, indent = '\t', separators = (',', ': '))

