from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver

import logging

class BrowserNavigator:
	
	# Инициализирует браузер.
	def __InitializeWebDriver(self):
		# Закрытие браузера.
		self.close()
		# Опции веб-браузера.
		ChromeOptions = Options()
		
		# Если указано настройками, включить AdBlock.
		if self.__Settings["adblock"] == True:
			ChromeOptions.add_extension('Libs/AdBlock.crx')

		# Установка опций.
		ChromeOptions.add_argument("--no-sandbox")
		ChromeOptions.add_argument("--disable-dev-shm-usage")
		ChromeOptions.add_argument("--disable-gpu")
		ChromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])
		
		# При отключённом режиме отладки скрыть окно браузера.
		if self.__Settings["debug"] is False:
			ChromeOptions.add_argument("--headless=new")

		try:
			# Инициализация браузера.
			self.__Browser = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = ChromeOptions)
			# Установка размера окна браузера на FullHD для корректной работы сайтов.
			self.__Browser.set_window_size(1920, 1080)
			# Установка максимального времени загрузки страницы и выполнения скрипта.
			self.__Browser.set_page_load_timeout(self.__Settings["timeout"])
			self.__Browser.set_script_timeout(self.__Settings["timeout"])
			
		except FileNotFoundError:
			# Запись в лог критической ошибки: неверный путь к вдрайверу.
			logging.critical("Unable to locate webdriver! Try to remove \".wdm\" folder in script directory.")
			
	# Конструктор: задаёт глобальные настройки и экземпляр браузера.
	def __init__(self, Settings: dict):

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		
		# Инициализация браузера.
		self.__InitializeWebDriver()
		
	# Закрывает браузер.
	def close(self):
		try:
			# Закрытие браузера.
			self.__Browser.close()
			self.__Browser.quit()
			
		except Exception:
			pass
		
	# Асинхронно выполняет JavaScript.
	def executeAsyncJavaScript(self, Script: str):
		# Результат выполнения скрипта.
		Result = None
		# Количество повторов.
		TriesCount = 0
		# Состояние: вернул ли скрипт ответ.
		IsLoaded = False
		
		# Повторять, пока скрипт не вернёт ответ.
		while IsLoaded == False:
				
			try:
				# Выполнение скрипта и запись результата.
				Result = self.__Browser.execute_async_script(Script)
					
			except Exception as ExceptionDescription:
				# Сохранение только первой строки исключения.
				ExceptionDescription = str(ExceptionDescription).split('\n')[0].strip(" \n.\t")
				# Инкремент количества повторов.
				TriesCount += 1
				# Запись в лог ошибки: содержимое ошибки.
				logging.error(f"\"{ExceptionDescription}\".")
				# Запись в лог ошибки: не удалось загрузить страницу.
				logging.error(f"Unable to execute async script: {TriesCount} retry...")
					
				# Если достигнуто максимальное количество повторов, выбросить исключение.
				if TriesCount == self.__Settings["retry-tries"]:
					raise TimeoutError("unable to execute async script")
			
			else:
				# Переключение статуса загрузки страницы.
				IsLoaded = True
				
		return Result

	# Возвращает HTML код тела страницы после полной загрузки.
	def getBodyHTML(self) -> str:
		# HTML код тела страницы после полной загрузки.
		BodyHTML = str(self.__Browser.execute_script("return document.body.innerHTML;"))

		return BodyHTML

	# Выполняет переход на указанную страницу.
	def loadPage(self, URL: str) -> int:
		# Состояние: выполняются ли условия перехода по URL.
		LoadCondition = True
		# Состояние: загружена ли страница.
		IsLoaded = False
		# Статус ответа.
		StatusCode = None

		# Проверка условия перехода: браузер находится на той же странице.
		if self.__Browser.current_url == URL:
			LoadCondition = False

		# Проверка условия перехода: сдвиг равен нулю и браузер находится на той же странице.
		if self.__Browser.current_url == URL.replace("?offset=0", ""):
			LoadCondition = False

		# Если все условия выполнены.
		if LoadCondition == True:
			# Количество повторов.
			TriesCount = 0

			# Повторять, пока страница не загружена.
			while IsLoaded == False:
				
				try:
					# Переход на страницу.
					self.__Browser.get(URL)
					# Установка статуса запроса.
					StatusCode = 200
					
					# Если страница содержит сообщение об ошибочной ссылке.
					if "Это ошибочная ссылка." in self.getBodyHTML():
						StatusCode = 404
					
				except Exception as ExceptionDescription:
					# Сохранение только первой строки исключения.
					ExceptionDescription = str(ExceptionDescription).split('\n')[0].strip(" \n.\t")
					# Установка статуса запроса.
					StatusCode = 408
					# Инкремент количества повторов.
					TriesCount += 1
					# Запись в лог ошибки: содержимое ошибки.
					logging.error(f"\"{ExceptionDescription}\".")
					# Запись в лог ошибки: не удалось загрузить страницу.
					logging.error(f"Unable to load page: {TriesCount} retry...")
					# Инициализация браузера.
					self.__InitializeWebDriver()
					
					# Если достигнуто максимальное количество повторов, выбросить исключение.
					if TriesCount == self.__Settings["retry-tries"]:
						raise TimeoutError("unable to load page")
			
				else:
					# Переключение статуса загрузки страницы.
					IsLoaded = True
					
		return StatusCode