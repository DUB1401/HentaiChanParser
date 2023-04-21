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

	# Возвращает структуру главы.
	def __GetChapter(self, ChapterSlug: str) -> dict:
		# Переход на страницу главы.
		self.__Navigator.LoadPage("https://hentaichan.live/manga/" + ChapterSlug + ".html")
		# HTML код тела страницы после полной загрузки.
		BodyHTML = self.__Navigator.GetBodyHTML()
		# Парсинг HTML кода страницы.
		Soup = BeautifulSoup(BodyHTML, "lxml")
		# Поиск блока переводчика.
		TranslatorBlock = Soup.find("span", {"class": "translation"})
		# Поиск блока названия главы.
		NameBlock = Soup.find("a", {"class": "title_top_a"})
		# Парсинг HTML кода блока переводчика.
		Soup = BeautifulSoup(str(TranslatorBlock), "lxml")
		# Поиск ссылки на переводчика.
		TranslatorBlock = Soup.find("a")
		# Структура главы.
		ChapterStruct = {
			"id": self.__GetChapterID(ChapterSlug),
			"number": None,
			"volume": None,
			"name": None,
			"is-paid": False,
			"translator": None,
			"slides": None
			}

		# Получение номера главы.
		ChapterStruct["number"] = self.__GetChapterNumber(NameBlock.get_text())
		# Получение ника переводчика.
		ChapterStruct["translator"] = TranslatorBlock.get_text()
		# Получение слайдов главы.
		ChapterStruct["slides"] = self.__GetChapterSlides(ChapterSlug)

		# Преобразование номера главы в числовое.
		if '.' in ChapterStruct["number"]:
			ChapterStruct["number"] = float(ChapterStruct["number"])
		else:
			ChapterStruct["number"] = int(ChapterStruct["number"])

		# Если переводчика нет, то обнулить значение.
		if ChapterStruct["translator"].strip(' ') == "":
			ChapterStruct["translator"] = None

		return ChapterStruct

	# Возвращает ID главы (определяется по алиасу).
	def __GetChapterID(self, ChapterSlug: str) -> int:
		# ID главы.
		ChapterID = None
		# Получение предполагаемого ID главы методом разбиения алиаса по знакам минуса.
		ChapterID = ChapterSlug.split('-')[0]

		try:
			# Попытка преобразования ID в число.
			ChapterID = int(ChapterID)

		except ValueError:
			# Обнуление ID.
			ChapterID = None
			# Запись в лог ошибки: не удалось получить ID главы.
			logging.error("Chapter: \"" + ChapterSlug + "\". Unable to found ID.")

		return ChapterID

	# Возвращает номер главы.
	def __GetChapterNumber(self, ChapterName: str) -> str:
		# Номер главы.
		ChapterNumber = None
		# Список вариаций написания главы.
		ChapterVariations = ["Глава", "глава", "Часть", "часть"]
		# Список ругулярных выражений для поиска номера главы.
		ChapterNumberReList = [r"глава \d+(\.)?(\d+)?", r"\d+(\.)?(\d+)? глава", r"часть \d+(\.)?(\d+)?", r"\d+(\.)?(\d+)? часть"]
	
		# Поиск вариантов написания номера главы.
		for Index in range(0, len(ChapterNumberReList)):
			# Буфер поиска.
			Bufer = re.search(ChapterNumberReList[Index], ChapterName, re.IGNORECASE)

			# Если буфер валиден, то сохранить значение.
			if Bufer != None:
				ChapterNumber = Bufer.group(0)

		# Удаление вариантов написания главы.
		for ChapterVariation in ChapterVariations:
			ChapterNumber = ChapterNumber.replace(ChapterVariation, "").strip()

		try:

			# Попытка преобразовать значение в числовое.
			if '.' in ChapterNumber:
				float(ChapterNumber)
			else:
				int(ChapterNumber)

		except ValueError:
			# Обнуление названия главы.
			ChapterNumber = None

		return ChapterNumber

	# Дополняет тайтл ветвями и главами.
	def __GetChaptersData(self, ChaptersSlugs: list):
		# Список глав.
		ChaptersList = list()
		# Список ветвей.
		Branches = list()
		# Структура глав.
		Chapters = dict()
		# Словарь глав согласно переводчикам.
		TranslatorsChaptersGroups = dict()

		# Для каждого алиаса создать структуру главы.
		for Slug in ChaptersSlugs:
			ChaptersList.append(self.__GetChapter(Slug))

		# Распределение глав по переводчикам.
		for Chapter in ChaptersList:
			# Никнейм текущего переводчика.
			CurrentTranslator = Chapter["translator"]

			# Создание списка под ключём переводчика.
			if CurrentTranslator not in TranslatorsChaptersGroups.keys():
				TranslatorsChaptersGroups[CurrentTranslator] = list()

			# Добавление главы в словарь по переводчику.
			TranslatorsChaptersGroups[CurrentTranslator].append(Chapter)

		# Индекс обрабатываемой ветви.
		CurrentBranchIndex = 1

		# Создание ветвей.
		for TranslatorChaptersGroupKey in TranslatorsChaptersGroups.keys():
			# Буфер ветви.
			BranchBufer = dict()
			# Запись ID ветви.
			BranchBufer["id"] = int(str(self.__ID) + str(CurrentBranchIndex).rjust(3, '0'))
			# Запись количества глав в ветви.
			BranchBufer["chapters-count"] = len(TranslatorsChaptersGroups[TranslatorChaptersGroupKey])
			# Запись буфера в список ветвей.
			Branches.append(BranchBufer)
			# Инкремент индекса ветви.
			CurrentBranchIndex += 1

		# Создание структуры глав.
		for BranchIndex in range(0, len(Branches)):
			Chapters[str(Branches[BranchIndex]["id"])] = TranslatorsChaptersGroups[list(TranslatorsChaptersGroups.keys())[BranchIndex]]

		# Запись ветвей.
		self.__Title["branches"] = Branches
		# Запись структуры глав.
		self.__Title["chapters"] = Chapters

		# Если автоматическое объединение ветвей включено.
		if len(Branches) > 0 and self.__Settings["auto-branches-merging"] == True:
			# Список ветвей после объединения.
			NewBranches = list()
			# Структура глав после объединения ветвей.
			NewChapters = dict()
			# Помещение в первую ветвь всех глав.
			NewChapters[list(Chapters.keys())[0]] = ChaptersList
			# Список номеров глав в первой ветви.
			FirstBranchChaptersNumbers = list()
			# Результирующая первая ветвь.
			ResultFirstBranch = list()
			# Словарь дублирующихся глав по переводчикам.
			DuplicatedChaptersGroups = dict()

			# Для каждой главы проверить дубли.
			for Chapter in NewChapters[list(Chapters.keys())[0]]:

				# Если главы с таким номером нет в первой ветви.
				if str(Chapter["number"]) not in FirstBranchChaptersNumbers:
					# Добавление номера главы в список номеров глав первой ветви.
					FirstBranchChaptersNumbers.append(str(Chapter["number"]))
					# Добавление текущей главы в результирующую первую ветвь.
					ResultFirstBranch.append(Chapter)

				# Если глава с таким номером уже есть в первой ветви.
				else:

					# Если ключа с таким переводчиком нет, то создать его.
					if Chapter["translator"] not in DuplicatedChaptersGroups.keys():
						DuplicatedChaptersGroups[Chapter["translator"]] = list()

					# Добавление текущей главы в словарь дублирующихся по переводчику.
					DuplicatedChaptersGroups[Chapter["translator"]].append(Chapter)

			# Помещение в первую ветвь результата слияния.
			NewChapters[list(Chapters.keys())[0]] = ResultFirstBranch
			# Индекс обрабатываемой ветви.
			CurrentBranchIndex = 1

			# Создание ветвей.
			for NewChaptersKey in NewChapters.keys():
				# Буфер ветви.
				BranchBufer = dict()
				# Запись ID ветви.
				BranchBufer["id"] = int(str(self.__ID) + str(CurrentBranchIndex).rjust(3, '0'))
				# Запись количества глав в ветви.
				BranchBufer["chapters-count"] = len(NewChapters[NewChaptersKey])
				# Запись буфера в список ветвей.
				NewBranches.append(BranchBufer)
				# Инкремент индекса ветви.
				CurrentBranchIndex += 1

			# Дополнение структуры глав.
			for BranchIndex in range(1, len(NewBranches)):
				NewChapters[str(NewBranches[BranchIndex]["id"])] = DuplicatedChaptersGroups[DuplicatedChaptersGroups.keys()[BranchIndex - 1]]

			# Запись ветвей.
			self.__Title["branches"] = NewBranches
			# Запись структуры глав.
			self.__Title["chapters"] = NewChapters

	# Возвращает структуру слайдов главы.
	def __GetChapterSlides(self, ChapterSlug: str) -> list:
		# Структура слайдов согласно формату DMP-V1.
		SlidesStruct = list()
		# Количество слайдов.
		SlidesCount = self.__GetChapterSlidesCount(ChapterSlug)

		# Для каждого слайда составить структуру.
		for SlideIndex in range(1, SlidesCount + 1):
			# Переход на страницу слайда.
			self.__Navigator.LoadPage("https://hentaichan.live/online/" + ChapterSlug + ".html?page=" + str(SlideIndex))
			# HTML код тела страницы после полной загрузки.
			BodyHTML = self.__Navigator.GetBodyHTML()
			# Парсинг HTML кода страницы.
			Soup = BeautifulSoup(BodyHTML, "lxml")
			# Поиск блока со слайдом.
			SlideBlock = Soup.find("img", {"style": "max-width:1000px;background-color:white;"})
			# Буферная структура слайда.
			SlideInfo = {
				"index": SlideIndex,
				"link": None,
				"width": None,
				"height": None
				}

			# Если слайд является изображением, то получить ссылку на него.
			if SlideBlock != None:
				SlideInfo["link"] = SlideBlock["src"]

			# Иначе считать, что содержимое слайда – видео.
			else:
				# Поиск блока с видео.
				SlideBlock = Soup.find("source", {"type": "video/mp4"})

				# Если слайд не является ни изображением, ни видео.
				if SlideBlock != None:
					SlideInfo["link"] = SlideBlock["src"]
				else:
					# Обнуление ссылки.
					SlideInfo["link"] = None
					# Запись в лог ошибки: не удалось определить тип слайда или слайд отсутствует.
					logging.error("Chapter: \"" + ChapterSlug + "\". Unable to determine slide type or slide missing on page: \"" + str(SlideIndex) + "\".")

			# Запись буфера в общую структуру.
			SlidesStruct.append(SlideInfo)

		return SlidesStruct

	# Возвращает количество слайдов в главе.
	def __GetChapterSlidesCount(self, ChapterSlug: str) -> int:
		# Количество слайдов в главе.
		SlidesCount = 0
		# Переход на страницу чтения главы.
		self.__Navigator.LoadPage("https://hentaichan.live/online/" + ChapterSlug + ".html")
		# HTML код тела страницы после полной загрузки.
		BodyHTML = self.__Navigator.GetBodyHTML()
		# Парсинг HTML кода страницы.
		Soup = BeautifulSoup(BodyHTML, "lxml")
		# Поиск блока со слайдами.
		SlidesBlock = Soup.find("div", {"id": "thumbs"})
		# Парсинг блока со слайдами.
		Soup = BeautifulSoup(str(SlidesBlock), "lxml")
		# Подсчёт количества слайдов в главе по количеству ссылок на них.
		SlidesCount = len(Soup.find_all("a"))
		
		return SlidesCount

	# Возвращает список алиасов глав тайтла.
	def __GetChaptersList(self) -> list:
		# Список URL глав тайтла.
		ChaptersList = list()
		# URL всех глав тайтла или похожих тайтлов.
		TitleURL = "https://hentaichan.live/related/" + self.__Slug + ".html"
		# Переход на страницу всех глав тайтла или похожих тайтлов.
		self.__Navigator.LoadPage(TitleURL)
		# HTML код тела страницы после полной загрузки.
		PageHTML = self.__Navigator.GetBodyHTML()
		
		# Если у тайтла одна глава.
		if "Хентай похожий на" in str(PageHTML):
			# Запись URL единственной главы.
			ChaptersList.append(self.__Slug)
			
		# Если у тайтла больше одной главы.
		else:
			# Количество страниц в каталоге глав тайтла.
			RelatedPagesCount = self.__GetRelatedPagesCount()
			
			# Получение URL глав с каждой страницы.
			for PageNumber in range(0, RelatedPagesCount):
				# Переход на страницу тайтла.
				self.__Navigator.LoadPage("https://hentaichan.live/related/" + self.__Slug + ".html?offset=" + str(10 * PageNumber))
				# HTML код тела страницы после полной загрузки.
				PageHTML = self.__Navigator.GetBodyHTML()
				# Парсинг HTML кода тела страницы.
				Soup = BeautifulSoup(PageHTML, "lxml")
				# Поиск блоков с информацией о главах.
				ChaptersBlocks = Soup.find_all("div", {"class": "related_info"})
				
				# Для каждой главы получить алиас.
				for Chapter in ChaptersBlocks:
					# Парсинг HTML блока с информацией о главе.
					SmallSoup = BeautifulSoup(str(Chapter), "lxml")
					# Поиск заголовка главы.
					Header = SmallSoup.find("h2")
					# Парсинг заголовка названия главы.
					SmallSoup = BeautifulSoup(str(Header), "lxml")
					# Поиск ссылки на главу.
					CapterLink = SmallSoup.find("a")

					# Если HTML ссылка найдена, и у неё есть адрес, то получить полный алиас.
					if CapterLink != None and CapterLink.has_attr("href"):
						ChaptersList.append(CapterLink["href"].replace("/manga/", "").replace(".html", ""))

		return ChaptersList

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
		PageHTML = self.__Navigator.GetBodyHTML()
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
		self.__Title["id"] = self.__ID
		self.__Title["slug"] = self.__Slug
		self.__Title["covers"] = self.__GetCoverData(PageHTML)
		self.__Title["ru-name"] = ParcedTitleName["ru-name"]
		self.__Title["en-name"] = ParcedTitleName["en-name"]
		self.__Title["another-names"] = ParcedTitleName["another-names"]
		self.__Title["type"]
		self.__Title["age-rating"] = 18
		self.__Title["publication-year"]
		self.__Title["status"]
		self.__Title["description"] = Description
		self.__Title["is-licensed"] = False
		self.__Title["genres"] = GenresAndTags["genres"]
		self.__Title["tags"] = GenresAndTags["tags"]

		# Запись в лог сообщения: получено описание тайтла.
		logging.info("Title: \"" + self.__Slug + "\". Request title description... Done.")

	# Возвращает количество страниц в каталоге глав тайтла.
	def __GetRelatedPagesCount(self) -> int:
		# Переход на страницу тайтла.
		self.__Navigator.LoadPage("https://hentaichan.live/related/" + self.__Slug + ".html")
		# HTML код тела страницы после полной загрузки.
		PageHTML = self.__Navigator.GetBodyHTML()
		# Парсинг HTML кода тела страницы.
		Soup = BeautifulSoup(PageHTML, "lxml")
		# Поиск HTML блока навигации по страницам.
		Pages = Soup.find_all("div", {"id" : "pagination_related"})
		# Парсинг HTML блока навигации.
		SmallSoup = BeautifulSoup(str(Pages), "lxml")
		# Поиск HTML ссылок на страницы.
		PagesLinks = SmallSoup.find_all("a")
		# Количество страниц (добавляется 1 для компенсации отсутствия в списке первой страницы).
		PagesCount = len(PagesLinks) + 1

		return PagesCount

	# Возвращает структуру из русского, английского и других названий тайтла.
	# TODO: считать название английским при совпадении более 50% слов со словарными образцами.
	def __ParceTitleName(self, TitleName: str) -> dict:
		# Список ругулярных выражений для поиска номера главы.
		ChapterNumberReList = [r"глав[аы] \d+([\.-])?(\d+)?", r"\d+([\.-])?(\d+)? глав[аы]", r"част[иь] \d+([\.-])?(\d+)?", r"\d+([\.-])?(\d+)? част[иь]", r"Ch. \d+([\.-])?(\d+)?"]
		# Поиск части названия в скобочках.
		BracketsPart = re.search("(?<=\()(.*?)(?=\))", TitleName, re.IGNORECASE)
		# Части названия.
		NamePartsList = list()
		# Буфер имён после удаления номера главы.
		NameBufer = list()
		# Структура названий.
		TitleNameStruct = {
			"ru-name": None,
		    "en-name": None,
		    "another-names": None
			}

		# Если есть часть названия в скобочках.
		if BracketsPart != None:
			# Преобразование в текст части названия в скобочках.
			BracketsPart = BracketsPart.group(0)
			# Удаление из заголовка части названия в скобочках.
			TitleName = TitleName.replace("(" + BracketsPart + ")", "")
			# Очистка краевых пробельных символов заголовка.
			TitleName = TitleName.strip()
			# Запись названия в скобочках как полноценного.
			NamePartsList.append(BracketsPart)
			# Запись названия без скобочек как полноценного.
			NamePartsList.append(TitleName)

		# Если название не содержит части в скобочках.
		else:
			# Запись названия тайтла для дальнейшей обработки.
			NamePartsList.append(TitleName)

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
		
		#---> Получение данных о тайтле.
		#==========================================================================================#
		# Запись в лог сообщения: парсинг начат.
		logging.info("Title: \"" + self.__Slug + "\". Parcing...")
		# Список глав в тайтле.
		ChaptersSlugs = self.__GetChaptersList()
		# Установка алиаса первой главы как основного для тайтла.
		self.__Slug = ChaptersSlugs[0]
		# Установка ID первой главы как основного для тайтла.
		self.__ID = self.__GetChapterID(self.__Slug)
		# Получение описательных данных тайтла.
		self.__GetTitleData()
		# Получение данных глав тайтла.
		self.__GetChaptersData(ChaptersSlugs)

	# Сохраняет локальный JSON файл.
	def Save(self):

		# Используемое имя тайтла: ID или алиас.
		UsedTitleName = None

		# Установка используемого имени тайтла.
		if self.__Settings["use-id-instead-slug"] == False:
			UsedTitleName = self.__Title["slug"]
		else:
			UsedTitleName = self.__ID

		# Сохранение локального файла JSON.
		with open(self.__Settings["titles-directory"] + UsedTitleName + ".json", "w", encoding = "utf-8") as FileWrite:
			json.dump(self.__Title, FileWrite, ensure_ascii = False, indent = '\t', separators = (',', ': '))