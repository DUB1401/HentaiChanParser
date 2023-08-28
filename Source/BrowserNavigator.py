from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import logging

class BrowserNavigator:
	
	# Инициализирует браузер.
	def __InitializeWebDriver(self):
		# Закрытие браузера.
		self.close()
		# Опции веб-драйвера.
		ChromeOptions = Options()
		# Установка опций.
		ChromeOptions.add_argument("disable-infobars")
		ChromeOptions.add_argument("--no-sandbox")
		ChromeOptions.add_argument("--disable-dev-shm-usage")
		ChromeOptions.add_argument("--disable-gpu")
		ChromeOptions.add_argument("--disable-extensions")
		ChromeOptions.add_argument('--disable-application-cache')
		ChromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])
		ChromeOptions.page_load_strategy = "eager"
		
		# При отключённом режиме отладки скрыть окно браузера.
		if self.__Settings["debug"] is False:
			ChromeOptions.add_argument("--headless=new")

		try:
			# Инициализация браузера.
			self.__Browser = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = ChromeOptions)
			# Установка размера окна браузера на FullHD для корректной работы сайтов.
			self.__Browser.set_window_size(1920, 1080)
			
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
	def executeAsyncJS(self, Script: str):
		# Выполнение скрипта и запист результата.
		Result = self.__Browser.execute_async_script(Script)

		return Result

	# Возвращает HTML код тела страницы после полной загрузки.
	def getBodyHTML(self) -> str:
		# HTML код тела страницы после полной загрузки.
		BodyHTML = str(self.__Browser.execute_script("return document.body.innerHTML;"))

		return BodyHTML

	# Выполняет переход на указанную страницу.
	def loadPage(self, URL: str):
		# Состояние: выполняются ли условия перехода по URL.
		LoadCondition = True
		# Состояние: загружена ли страница.
		IsLoaded = False

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
					
				except Exception:
					# Инкремент количества повторов.
					TriesCount += 1
					# Запись в лог: не удалось загрузить страницу.
					logging.error("Unable to load page. Retry...")
					# Инициализация браузера.
					self.__InitializeWebDriver()
					
					# Если достигнуто максимальное количество повторов, выбросить исключение.
					if TriesCount == self.__Settings["retry-tries"]:
						raise TimeoutError("unable to load page")
			
				else:
					# Переключение статуса загрузки страницы.
					IsLoaded = True