from dublib.Methods import CheckForCyrillicPresence, Cls, ReadJSON, RemoveRecurringSubstrings, WriteJSON
from Source.Functions import GetImageResolution
from dublib.WebRequestor import WebRequestor
from dublib.Polyglot import HTML
from collections import Counter
from bs4 import BeautifulSoup

import requests
import enchant
import logging
import shutil
import json
import os
import re

# Парсер тайтлов.
class TitleParser:

	# Дополняет главы данными о слайдах.
	def __AmendChapters(self):
		# Запись в лог сообщения: дополнение глав информацией о слайдах начато.
		logging.info("Title: \"" + self.__Slug + "\". Amending...")
		# Список ветвей.
		BranchesID = self.__Title["chapters"].keys()
		# Количество дополненных глав.
		AmendedChaptersCount = 0
		# Общее количество глав.
		TotalChaptersCount = self.__GetTotalChaptersCount()

		# Для каждой ветви.
		for BranchID in BranchesID:
			
			# Для каждой главы.
			for ChapterIndex in range(0, len(self.__Title["chapters"][BranchID])):
				# Очистка консоли.
				Cls()
				# Вывод в терминал: прогресс дополнения.
				print(self.__Message + "\nAmending chapters: " + str(AmendedChaptersCount + 1) + " / " + str(TotalChaptersCount))

				# Если в главе нет данных о слайдах.
				if self.__Title["chapters"][BranchID][ChapterIndex]["slides"] == list():
					# Алиас главы.
					ChapterSlug = self.__FindChapterSlugInList(self.__Title["chapters"][BranchID][ChapterIndex]["id"])
					# Получение данных о слайдах.
					self.__Title["chapters"][BranchID][ChapterIndex]["slides"] = self.__GetChapterSlides(ChapterSlug)
					# Состояние: повторять ли запрос данных.
					RepeatRequest = False
					
					# Для каждого слайда.
					for Slide in self.__Title["chapters"][BranchID][ChapterIndex]["slides"]:
						
						# Если у слайда нет ссылки и необходимо повторить запрос.
						if Slide["link"] == None and RepeatRequest == False:
							# Проведение повторного запроса данных.
							self.__Title["chapters"][BranchID][ChapterIndex]["slides"] = self.__GetChapterSlides(ChapterSlug)
							# Запись в лог предупреждения: повторный запрос данных о главе.
							logging.warning("Title: \"" + self.__Slug + "\". Unable to find slide data. Repeat request... ")

					# Инкремент количества дополненных глав.
					AmendedChaptersCount += 1
					# Запись в лог сообщения: глава дополнена.
					logging.info("Title: \"" + self.__Slug + "\". Chapter " + str(self.__Title["chapters"][BranchID][ChapterIndex]["id"]) + " amended.")

		# Запись в лог сообщения: количество дополненных глав.
		logging.info("Title: \"" + self.__Slug + "\". Amended chapters: " + str(AmendedChaptersCount) + ".")

	# Возвращает алиас главы по её ID.
	def __FindChapterSlugInList(self, ChapterID: int) -> str:
		# Искомый алиас.
		SearchableSlug = None

		# Поиск алиаса с указанным ID.
		for Slug in self.__ChaptersSlugs:
			if str(ChapterID) in Slug:
				SearchableSlug = Slug

		return SearchableSlug

	# Форматирует указанные настройками теги в жанры.
	def __FindGenres(self):
		# Удаляемые теги.
		TagsToDeleting = list()
		
		# Проход по всем тегам и названиям жанров.
		for TagIndex in range(0, len(self.__Title["tags"])):
			for GenreName in list(self.__Settings["genres"].keys()):

				# Если название тега совпадает с название жанра.
				if self.__Title["tags"][TagIndex] == GenreName.lower():
					# Запись тега для последующего удаления.
					TagsToDeleting.append(self.__Title["tags"][TagIndex])
					
					# Если тег не нужно переименовать в жанр.
					if self.__Settings["genres"][GenreName.lower()] == None:
						self.__Title["genres"].append(self.__Title["tags"][TagIndex])

					# Если тег нужно переименовать в жанр.
					else:
						self.__Title["genres"].append(self.__Settings["genres"][GenreName.lower()])

		# Удаление ненужных тегов.
		for Tag in TagsToDeleting:
			self.__Title["tags"].remove(Tag)

	# Возвращает автора.
	def __GetAuthor(self, Soup: BeautifulSoup):
		# Никнейм автора.
		Author = None
		# Поиск блока информации о главе.
		InfoBlock = Soup.find("div", {"id": "info_wrap"})
		# Парсинг HTML кода блока информации о главе.
		Soup = BeautifulSoup(str(InfoBlock), "html.parser")
		# Поиск ссылки на автора.
		AuthorBlock = Soup.find_all("a")[2]
		# Получение автора.
		Author = AuthorBlock.get_text()

		# Проверка на отсутствие автора.
		if Author == "Unknown":
			Author = None

		return Author

	# Возвращает структуру главы.
	def __GetChapter(self, ChapterSlug: str) -> dict:
		# Запрос страницы главы.
		Response = self.__Navigator.get("https://hentaichan.live/manga/" + ChapterSlug + ".html")
		# Парсинг HTML кода страницы.
		Soup = BeautifulSoup(Response.text, "html.parser")
		# Поиск блока переводчика.
		TranslatorBlock = Soup.find("span", {"class": "translation"})
		# Поиск блока названия главы.
		NameBlock = Soup.find("a", {"class": "title_top_a"})
		# Парсинг HTML кода блока переводчика.
		Soup = BeautifulSoup(str(TranslatorBlock), "html.parser")
		# Поиск ссылки на переводчика.
		TranslatorBlock = Soup.find("a")
		# Структура главы.
		ChapterStruct = {
			"id": self.__GetChapterID(ChapterSlug),
			"volume": None,
			"number": None,
			"name": None,
			"is-paid": False,
			"translator": None,
			"slides": None
			}

		# Получение номера главы.
		ChapterStruct["number"] = self.__GetChapterNumber(NameBlock.get_text())
		# Получение слайдов главы.
		ChapterStruct["slides"] = list()
		
		# Если присутствует никнейм переводчика, то записать его.
		if TranslatorBlock != None:
			ChapterStruct["translator"] = TranslatorBlock.get_text().strip()

		# Преобразование номера главы в числовое.
		if ChapterStruct["number"] != None and '.' in ChapterStruct["number"]:
			ChapterStruct["number"] = float(ChapterStruct["number"])
		elif ChapterStruct["number"] != None:
			ChapterStruct["number"] = int(ChapterStruct["number"])

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
		# Список возможных номеров главы.
		ChapterNumber = list()
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
				ChapterNumber.append(Bufer.group(0))

		# Удаление вариантов написания главы.
		if len(ChapterNumber) != 0:
			for NumberIndex in range(0, len(ChapterNumber)):
				for ChapterVariation in ChapterVariations:
					ChapterNumber[NumberIndex] = ChapterNumber[NumberIndex].replace(ChapterVariation, "").strip()

				try:

					# Попытка преобразовать значение в числовое.
					if '.' in ChapterNumber[NumberIndex]:
						float(ChapterNumber[NumberIndex])
					else:
						int(ChapterNumber[NumberIndex])

				except ValueError:
					# Удаление номера главы из списка.
					ChapterNumber.remove(ChapterNumber[NumberIndex])

		# Обнуление номера главы в случае неудачного обнаружения.
		if len(ChapterNumber) == 0:
			ChapterNumber = None

		# Определение наибольшего из возможных номеров главы (исправляет проблему с двумя и более разными номерами главы).
		else:
			ChapterNumber = str(max(ChapterNumber)).strip('.')

		return ChapterNumber

	# Дополняет тайтл ветвями и главами.
	def __GetChaptersData(self):
		# Список глав.
		ChaptersList = list()
		# Список ветвей.
		Branches = list()
		# Структура глав.
		Chapters = dict()
		# Словарь глав согласно переводчикам.
		TranslatorsChaptersGroups = dict()

		# Для каждого алиаса создать структуру главы.
		for Slug in self.__ChaptersSlugs:
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

		# Запись в лог сообщения: получены данные о главах.
		logging.info("Title: \"" + self.__Slug + "\". Request title branches... Done.")

	# Возвращает структуру слайдов главы.
	def __GetChapterSlides(self, ChapterSlug: str) -> list:
		# Структура слайдов согласно формату DMP-V1.
		SlidesStruct = list()
		# Запрос страницы первого слайда.
		Response = self.__Navigator.get("https://hentaichan.live/online/" + ChapterSlug + ".html?page=1")
		# Парсинг HTML кода страницы.
		Soup = BeautifulSoup(Response.text, "html.parser")
		# Поиск блоков скрипта.
		ScriptsBlocks = Soup.find_all("script")
		# JSON определений изображений.
		ImagesJSON = None
		
		# Для каждого скрипта на странице.
		for Script in ScriptsBlocks:
			
			# Если скрипт содержит определения слайдов.
			if "\"thumbs\": [" in str(Script):
				# Буфер обработки скрипта.
				Bufer = HTML(str(Script).replace("var data = ", "").replace("createGallery(data)", "")).plain_text.replace('\'', '"')
				# Форматировать скрипт в JSON.
				ImagesJSON = json.loads(Bufer)
		
		# Для каждого слайда составить структуру.
		for SlideIndex in range(0, len(ImagesJSON["fullimg"])):
			# Буферная структура слайда.
			SlideInfo = {
				"index": SlideIndex + 1,
				"link": ImagesJSON["fullimg"][SlideIndex],
				"width": None,
				"height": None
			}
			
			# Если используется WEBP.
			if self.__Settings["use-webp"] == True:
				# Изменить расширение файла в ссылке.
				SlideInfo["link"] = SlideInfo["link"].replace(".jpg", ".webp").replace(".jpeg", ".webp")

			# Запись в лог предупреждения: слайд является видео.
			if SlideInfo["link"].endswith(".mp4"): logging.warning("Chapter: \"" + ChapterSlug + "\". Slide " + str(SlideIndex + 1) + " is MP4 video.")
			# Запись буфера в общую структуру.
			SlidesStruct.append(SlideInfo)
		
		return SlidesStruct

	# Возвращает список алиасов глав тайтла.
	def __GetChaptersList(self) -> list:
		# Список URL глав тайтла.
		ChaptersList = list()
		# URL всех глав тайтла или похожих тайтлов.
		TitleURL = "https://hentaichan.live/related/" + self.__Slug + ".html"
		# Запрос страницы всех глав тайтла.
		Response = self.__Navigator.get(TitleURL)
		
		# Если запрос успешен.
		if Response.status_code == 200:
		
			# Если у тайтла одна глава.
			if "Хентай похожий на" in Response.text or "Похожая манга" in Response.text:
				# Запись URL единственной главы.
				ChaptersList.append(self.__Slug)
			
			# Если у тайтла больше одной главы.
			else:
				# Количество страниц в каталоге глав тайтла.
				RelatedPagesCount = self.__GetRelatedPagesCount()
			
				# Получение URL глав с каждой страницы.
				for PageNumber in range(0, RelatedPagesCount):
					# Запрос страницы с главами.
					PageResponse = self.__Navigator.get("https://hentaichan.live/related/" + self.__Slug + ".html?offset=" + str(10 * PageNumber))
					# Парсинг HTML кода тела страницы.
					Soup = BeautifulSoup(PageResponse.text, "html.parser")
					# Поиск блоков с информацией о главах.
					ChaptersBlocks = Soup.find_all("div", {"class": "related_info"})
				
					# Для каждой главы получить алиас.
					for Chapter in ChaptersBlocks:
						# Парсинг HTML блока с информацией о главе.
						SmallSoup = BeautifulSoup(str(Chapter), "html.parser")
						# Поиск заголовка главы.
						Header = SmallSoup.find("h2")
						# Парсинг заголовка названия главы.
						SmallSoup = BeautifulSoup(str(Header), "html.parser")
						# Поиск ссылки на главу.
						CapterLink = SmallSoup.find("a")

						# Если HTML ссылка найдена, и у неё есть адрес, то получить полный алиас.
						if CapterLink != None and CapterLink.has_attr("href"):
							ChaptersList.append(CapterLink["href"].replace("/manga/", "").replace(".html", ""))
							
		else:
			# Запись в лог предупреждения: тайтл не найден.
			logging.warning("Title: \"" + self.__Slug + "\". Not found. Skipped.")
			# Перевод тайтла в неактивный статус.
			self.__IsActive = False
			
		# Если не удалось обнаружить главы, добавить оригинальный алиас.
		if len(ChaptersList) == 0:
			ChaptersList.append(self.__Slug)

		return ChaptersList

	# Возвращает её описательную структуру в формате DMP-V1.
	def __GetCoverData(self, PageHTML: str) -> dict:
		# Контейнер обложек.
		CoversList = list()
		# Парсинг HTML кода тела страницы.
		Soup = BeautifulSoup(PageHTML, "html.parser")
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

			# Если у обложки есть источник.
			if str(CoverHTML["src"]) != "":
				# Заполнение данных обложки.
				Cover["link"] = str(CoverHTML["src"])
				Cover["filename"] = Cover["link"].split('/')[-1]
				CoversList.append(Cover)
				# Используемое имя тайтла: ID или алиас.
				UsedTitleName = str(self.__ID) if self.__Settings["use-id-instead-slug"] == True else self.__Slug
				
				# Если включено определение разрешение обложки.
				if self.__Settings["sizing-covers"] == True:
					# Определение разрешения.
					Resolution = GetImageResolution(self.__Settings["covers-directory"] + UsedTitleName + "/" + Cover["filename"])
					# Заполнение разрешения.
					Cover["width"] = Resolution["width"]
					Cover["height"] = Resolution["height"]

			# Если у обложки нет источника.
			else:
				# Запись в лог предупреждения: обложка отсутствует.
				logging.warning("Title: \"" + self.__Slug + "\". Cover missing.")

		return CoversList

	# Возвращает список тегов в формате DMP-V1.
	def __GetTags(self, PageHTML: str) -> list:
		# Список тегов.
		Tags = list()
		# Парсинг HTML кода тела страницы.
		Soup = BeautifulSoup(PageHTML, "html.parser")
		# Поиск всех HTML элементов тегов.
		AllTags = Soup.find_all("li", {"class": "sidetag"})

		# Для названия каждого тега удалить лишние символы.
		for Tag in AllTags:
			Tags.append(Tag.get_text().replace("\n", "").replace("+-", ""))
		
		return Tags

	# Заполняет информацию о тайтле.
	def __GetTitleData(self):
		# URL тайтла.
		TitleURL = "https://hentaichan.live/manga/" + self.__Slug + ".html"
		# Запрос страницы тайтла.
		Response = self.__Navigator.get(TitleURL)
		
		# Если запрос успешен.
		if Response.status_code == 200 and "здесь ничего нет. Это ошибочная ссылка." not in Response.text:
			# Парсинг HTML кода тела страницы.
			Soup = BeautifulSoup(Response.text, "html.parser")
			# Поиск HTML элемента названия тайтла.
			TitleName = Soup.find("a", {"class": "title_top_a"}).get_text()
			# Структура названия главы: русское, английское и другие.
			ParcedTitleName = self.__ParceTitleName(TitleName)
			# Поиск HTML элемента описания.
			DescriptionHTML = Soup.find("div", {"id": "description"})
			# Описание тайтла.
			Description = None
			# Получение структур жанров и тегов.
			Tags = self.__GetTags(Response.text)

			# Проверка наличия описания.
			if DescriptionHTML != None:

				# Удаление вложенных блоков из описания.
				for Block in DescriptionHTML.select("div"):
					Block.decompose()

				# Замена тегов на спецсимволы новой строки.
				DescriptionHTML = BeautifulSoup(str(DescriptionHTML).replace("<br/>", "\n"), "html.parser")
				# Получение оставшегося текста без краевых спецсимволов и пробелов.
				Description = DescriptionHTML.get_text().strip("\n \t")
				# Удаление повторяющихся символов новой строки.
				RemoveRecurringSubstrings(Description, '\n')
				# Удаление краевых пробельных символов.
				Description = Description.strip()
				# Если описание пустое, то обнулить его.
				if Description == "": Description = None
		
			# Заполнение полей описательной структуры.
			self.__Title["site"] = "hentaichan.live"
			self.__Title["id"] = self.__ID
			self.__Title["slug"] = self.__Slug
			self.__Title["covers"] = self.__GetCoverData(Response.text)
			self.__Title["ru-name"] = ParcedTitleName["ru-name"]
			self.__Title["en-name"] = ParcedTitleName["en-name"]
			self.__Title["another-names"] = ParcedTitleName["another-names"]
			self.__Title["author"] = self.__GetAuthor(Soup)
			self.__Title["publication-year"]
			self.__Title["age-rating"] = 18
			self.__Title["description"] = Description
			self.__Title["type"] = "UNKNOWN"
			self.__Title["status"] = "UNKNOWN"
			self.__Title["is-licensed"] = False
			self.__Title["series"] = self.__GetSeries(Soup)
			self.__Title["genres"] = list()
			self.__Title["tags"] = Tags

			# Форматирование указанных настройками тегов в жанры.
			self.__FindGenres()
			# Запись в лог сообщения: получено описание тайтла.
			logging.info("Title: \"" + self.__Slug + "\". Request title description... Done.")
			
		else:
			# Запись в лог предупреждения: тайтл не найден.
			logging.warning("Title: \"" + self.__Slug + "\". Not found. Skipped.")
			# Перевод тайтла в неактивный статус.
			self.__IsActive = False

	# Возвращает суммарное количество глав во всех ветвях.
	def __GetTotalChaptersCount(self) -> int:
		# Счётчик.
		CounterObject = Counter()

		# Подсчёт суммы глав во всех ветвях.
		for BranchDescription in self.__Title["branches"]:
			CounterObject.update(BranchDescription)

		# Суммарное количество глав во всех ветвях.
		TotalChaptersCount = dict(CounterObject)["chapters-count"]

		return TotalChaptersCount

	# Возвращает количество страниц в каталоге глав тайтла.
	def __GetRelatedPagesCount(self) -> int:
		# Запрос страницы тайтла.
		Response = self.__Navigator.get("https://hentaichan.live/related/" + self.__Slug + ".html")
		# Парсинг HTML кода тела страницы.
		Soup = BeautifulSoup(Response.text, "html.parser")
		# Поиск HTML блока навигации по страницам.
		Pages = Soup.find_all("div", {"id" : "pagination_related"})
		# Парсинг HTML блока навигации.
		SmallSoup = BeautifulSoup(str(Pages), "html.parser")
		# Поиск HTML ссылок на страницы.
		PagesLinks = SmallSoup.find_all("a")
		
		# Если кнопок перехода по страницам нет, то одна страница.
		if len(PagesLinks) == 0:
			PagesCount = 1
		
		# Если есть кнопки перехода по страницам, то вычесть кнопки навигации и добавить первую страниц.
		else:
			PagesCount = len(PagesLinks) + 1 - 2

		return PagesCount

	# Возвращает серию.
	def __GetSeries(self, Soup: BeautifulSoup):
		# Название серии.
		Series = list()
		# Поиск блока информации о главе.
		InfoBlock = Soup.find("div", {"id": "info_wrap"})
		# Парсинг HTML кода блока информации о главе.
		Soup = BeautifulSoup(str(InfoBlock), "html.parser")
		# Поиск ссылки на серию.
		AuthorBlock = Soup.find_all("a")[1]
		# Получение серии.
		SeriesName = AuthorBlock.get_text()

		# Проверка на отсутствие серии.
		if SeriesName != "Оригинальные работы":
			Series.append(SeriesName)

		return Series

	# Выполняет слияние ветвей локального файла и полученных с сервера.
	def __MergeBranches(self, LocalFilename: str):
		# Список локальных глав.
		LocalChaptersList = list()
		
		# Если включён режим перезаписи.
		if self.__ForceMode == True:
			# Запись в лог сообщения: найден локальный описательный файл тайтла.
			logging.info("Title: \"" + self.__Slug + "\". Local JSON already exists. Will be overwritten...")
			
		else:
			# Запись в лог сообщения: найден локальный описательный файл тайтла.
			logging.info("Title: \"" + self.__Slug + "\". Local JSON already exists. Trying to merge...")
			
		# Чтение локального файла.
		LocalTitle = ReadJSON(self.__Settings["titles-directory"] + LocalFilename + ".json")
		# Записать главы из каждой ветви.
		for BranchID in LocalTitle["chapters"].keys(): LocalChaptersList += LocalTitle["chapters"][BranchID]

		# Для каждой ветви.
		for BranchID in self.__Title["chapters"].keys():
			
			# Для каждой главы.
			for ChapterIndex in range(0, len(self.__Title["chapters"][BranchID])):
				# ID текущей главы.
				ChapterID = self.__Title["chapters"][BranchID][ChapterIndex]["id"]

				# Поиск данных о слайдах в локальных главах.
				for LocalChapter in LocalChaptersList:

					# Если ID обрабатываемой главы совпал с ID локальной главы.
					if ChapterID == LocalChapter["id"]:
						# Копирование данных о слайдах.
						self.__Title["chapters"][BranchID][ChapterIndex]["slides"] = LocalChapter["slides"]
						# Инкремент количества слияний.
						self.__MergedChaptersCount += 1

		# Запись в лог сообщения: завершение слияния.
		if self.__MergedChaptersCount > 0:
			logging.info("Title: \"" + self.__Slug + "\". Merged chapters: " + str(self.__MergedChaptersCount) + ".")
		else:
			logging.info("Title: \"" + self.__Slug + "\". There are no new chapters.")

	# Возвращает структуру из русского, английского и других названий тайтла.
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
		    "another-names": list()
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

		# Если часть названия содержит слеш, то разделить её.
		for Index in range(0, len(NamePartsList)):
			if '/' in NamePartsList[Index]:
				NamePartsList.append(NamePartsList[Index].split('/')[1])
				NamePartsList[Index] = NamePartsList[Index].split('/')[0]

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
				# Список слов в названии тайтла длинной более 2-ух символов.
				Words = list()
				# Количество слов, найденных в английском словаре.
				EnglishWordsCount = 0

				# Составление списка слов длинной более 2-ух символов.
				for Word in list(Name.split(' ')):
					if len(Word) > 2:
						Words.append(Word)

				# Проверка каждого слова длинной более 2-ух символов по словарю.
				for Word in Words:
					if DictEnUS.check(Word) == True:
						EnglishWordsCount += 1
				
				# Если больше половины слов английские, то считать часть названия английской.
				if EnglishWordsCount >= int(len(Words) / 3):
					TitleNameStruct["en-name"] = Name
					IsLocaled = True

			# Обработка: транслитерированное название.
			if IsLocaled == False:
				# Запись альтернативных названий через запятую.
				TitleNameStruct["another-names"].append(Name)

		return TitleNameStruct

	# Конструктор.
	def __init__(self, Settings: dict, Navigator: WebRequestor, Slug: str, ForceMode: bool = False, Message: str = "", Amending: bool = True):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Количество выполненных слияний глав.
		self.__MergedChaptersCount  = 0
		# Список алиасов глав тайтла.
		self.__ChaptersSlugs = list()
		# Состояние: включена ли перезапись файлов.
		self.__ForceMode = ForceMode
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Обработчик навигации.
		self.__Navigator = Navigator
		# Состояние: доступен ли тайтл.
		self.__IsActive = True
		# Описательная структура тайтла.
		self.__Title = {
			"format": "dmp-v1",
			"site": None,
			"id": None,
			"slug": None,
			"covers": list(),
			"ru-name": None,
			"en-name": None,
			"another-names": None,
			"author": None,
			"publication-year": None,
			"age-rating": None,
			"description": None,
			"type": None,
			"status": None,
			"is-licensed": None,
			"series": list(),
			"genres": list(),
			"tags": list(),
			"branches": list(),
			"chapters": dict()
		}
		# Алиас тайтла.
		self.__Slug = Slug
		# Сообщение из внешнего обработчика.
		self.__Message = Message + "Current title: " + self.__Slug + "\n"
		# ID тайтла.
		self.__ID = None
		
		# Очистка консоли.
		Cls()
		# Вывод в консоль: сообщение из внешнего обработчика и алиас обрабатываемого тайтла.
		print(self.__Message, end = "")
		
		#---> Получение данных о тайтле.
		#==========================================================================================#
		# Список глав в тайтле.
		self.__ChaptersSlugs = self.__GetChaptersList()
		# Установка алиаса первой главы как основного для тайтла.
		self.__Slug = self.__ChaptersSlugs[0]
		# Установка ID первой главы как основного для тайтла.
		self.__ID = self.__GetChapterID(self.__Slug)
		# Запись в лог сообщения: парсинг начат.
		logging.info("Title: \"" + self.__Slug + "\". Parcing...")
		# Получение описательных данных тайтла.
		self.__GetTitleData()
		
		# Если включена полная обработка файла.
		if Amending == True and self.__IsActive == True:
			# Получение данных глав тайтла.
			self.__GetChaptersData()
			
			# Если включён режим перезаписи.
			if ForceMode == False:

				# Слияние с локальным описательным файлом.
				if os.path.exists(self.__Settings["titles-directory"] + self.__Slug + ".json"):
					self.__MergeBranches(self.__Slug)
					
				elif os.path.exists(self.__Settings["titles-directory"] + str(self.__ID) + ".json"):
					self.__MergeBranches(str(self.__ID))

			# Дополняет главы данными о слайдах.
			self.__AmendChapters()

	# Загружает обложку тайтла.
	def downloadCover(self):
			
		# Если удалось получить доступ к тайтлу.
		if self.__IsActive == True:
			# Счётчик загруженных обложек.
			DownloadedCoversCounter = 0
			# Используемое имя тайтла: ID или алиас.
			UsedTitleName = None
			# Очистка консоли.
			Cls()
			# Вывод в консоль: сообщение из внешнего обработчика и алиас обрабатываемого тайтла.
			print(self.__Message, end = "")
		
			# Создание директории обложек, если таковая отсутствует.
			if os.path.exists(self.__Settings["covers-directory"]) == False:
				os.makedirs(self.__Settings["covers-directory"])

			# Установка используемого имени тайтла.
			if self.__Settings["use-id-instead-slug"] == False:
				UsedTitleName = self.__Slug
			
			else:
				UsedTitleName = str(self.__ID)

			# Для каждой обложки.
			for CoverIndex in range(0, len(self.__Title["covers"])):
				# URL обложки.
				CoverURL = self.__Title["covers"][CoverIndex]["link"]
				# Название файла обложки.
				CoverFilename = self.__Title["covers"][CoverIndex]["filename"]
				# Ответ запроса.
				Response = None

				# Если включён режим перезаписи, то удалить файл обложки.
				if self.__ForceMode == True:
					
					# Удалить файл обложки.
					if os.path.exists(self.__Settings["covers-directory"] + self.__Slug + "/" + CoverFilename):
						shutil.rmtree(self.__Settings["covers-directory"] + self.__Slug) 
					elif os.path.exists(self.__Settings["covers-directory"] + str(self.__ID) + "/" + CoverFilename):
						shutil.rmtree(self.__Settings["covers-directory"] + str(self.__ID)) 

				# Удаление папки для обложек с алиасом в названии, если используется ID.
				if self.__Settings["use-id-instead-slug"] == True and os.path.exists(self.__Settings["covers-directory"] + self.__Slug + "/" + CoverFilename):
					shutil.rmtree(self.__Settings["covers-directory"] + self.__Slug)

				# Удаление папки для обложек с ID в названии, если используется алиас.
				if self.__Settings["use-id-instead-slug"] == False and os.path.exists(self.__Settings["covers-directory"] + str(self.__ID) + "/" + CoverFilename):
					shutil.rmtree(self.__Settings["covers-directory"] + str(self.__ID))

				# Проверка существования файла обложки.
				if os.path.exists(self.__Settings["covers-directory"] + UsedTitleName + "/" + CoverFilename) == False:
					# Вывод в терминал URL загружаемой обложки.
					print("Downloading cover: \"" + CoverURL + "\"... ", end = "")
					# Выполнение запроса.
					Response = requests.get(CoverURL)

					# Проверка успешности запроса.
					if Response.status_code == 200:

						# Создание папки для обложек.
						if os.path.exists(self.__Settings["covers-directory"]) == False:
							os.makedirs(self.__Settings["covers-directory"])

						# Создание папки для конкретной обложки.
						if os.path.exists(self.__Settings["covers-directory"] + UsedTitleName) == False:
							os.makedirs(self.__Settings["covers-directory"] + UsedTitleName)

						# Открытие потока записи.
						with open(self.__Settings["covers-directory"] + UsedTitleName + "/" + CoverFilename, "wb") as FileWrite:
							# Запись изображения.
							FileWrite.write(Response.content)
							# Инкремент счётчика загруженных обложек.
							DownloadedCoversCounter += 1
							# Вывод в терминал сообщения об успешной загрузке.
							print("Done.")

					else:
						# Запись в лог сообщения о неудачной попытке загрузки обложки.
						logging.error("Title: \"" + self.__Slug + "\". Unable download cover: \"" + CoverURL + "\". Response code: " + str(Response.status_code) + ".")
						# Вывод в терминал сообщения об успешной загрузке.
						print("Failure!")

				else:
					# Вывод в терминал: URL загружаемой обложки.
					print("Cover already exist: \"" + CoverURL + "\". Skipped. ")

			# Запись в лог сообщения: количество загруженных обложек.
			logging.info("Title: \"" + self.__Slug + "\". Covers downloaded: " + str(DownloadedCoversCounter) + ".")

	# Сохраняет локальный JSON файл.
	def save(self):
		
		# Если удалось получить доступ к тайтлу.
		if self.__IsActive == True:
			# Используемое имя тайтла: ID или алиас.
			UsedTitleName = None

			# Создание директории тайтлов, если таковая отсутствует.
			if os.path.exists(self.__Settings["titles-directory"]) == False:
				os.makedirs(self.__Settings["titles-directory"])

			# Установка используемого имени тайтла.
			if self.__Settings["use-id-instead-slug"] == False:
				UsedTitleName = self.__Title["slug"]
			else:
				UsedTitleName = str(self.__ID)

			# Сохранение файла.
			WriteJSON(self.__Settings["titles-directory"] + UsedTitleName + ".json", self.__Title)

			# Запись в лог сообщения: создан или обновлён локальный файл.
			if self.__MergedChaptersCount > 0:
				logging.info("Title: \"" + self.__Slug + "\". Updated.")
				
			else:
				logging.info("Title: \"" + self.__Slug + "\". Parced.")