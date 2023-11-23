from fake_useragent import UserAgent as UserAgentGenerator
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver

import requests
import enum

#==========================================================================================#
# >>>>> ИСКЛЮЧЕНИЯ <<<<< #
#==========================================================================================#

class ConfigRequired(Exception):

	# Конструктор: вызывается при обработке исключения.
	def __init__(self):
		"""
		Исключение: не задана конфигурация.
		"""
	
		# Добавление данных в сообщение об ошибке.
		self.__Message = "Selenium or requests config required."
		# Обеспечение доступа к оригиналу наследованного свойства.
		super().__init__(self.__Message)
			
	# Преобразователь: представляет содержимое класса как строку.
	def __str__(self):
		return self.__Message

class SeleniumRequired(Exception):

	# Конструктор: вызывается при обработке исключения.
	def __init__(self):
		"""
		Исключение: не инициализирован Selenium.
		"""
	
		# Добавление данных в сообщение об ошибке.
		self.__Message = "Selenium webdriver initialization required."
		# Обеспечение доступа к оригиналу наследованного свойства.
		super().__init__(self.__Message)
			
	# Преобразователь: представляет содержимое класса как строку.
	def __str__(self):
		return self.__Message

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ ТИПЫ ДАННЫХ <<<<< #
#==========================================================================================#

# Перечисление типов поддерживаемых браузеров.
class Browsers(enum.Enum):
	Chrome = "Google Chrome"
	#Firefox = "Mozilla Firefox"
	#Edge = "Microsoft Edge"

# Конфигурация requests.
class RequestsConfig:
	
	# Конструктор.
	def __init__(self):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Заголовки запросов.
		self.Headers = {
			"User-Agent": str(UserAgentGenerator.chrome)
		}
		
	# Добавляет пользовательский заголовок запроса.
	def addHeader(self, Key: str, Value: int | str):
		# Запись заголовка.
		self.Headers[Key] = Value
		
	# Задаёт пользовательское значение заголовка Referer.
	def setReferer(self, Referer: str):
		self.Headers["Referer"] = Referer
		
	# Задаёт пользовательское значение заголовка User-Agent.
	def setUserAgent(self, UserAgent: str):
		self.Headers["User-Agent"] = UserAgent
	
# Конфигурация Selenium.
class SeleniumConfig:
	
	# Конструктор.
	def __init__(
			self,
		    BrowserType: Browsers = Browsers.Chrome,
		    Headless: bool = False,
		    PageLoadTimeout: int = 75,
			ScriptTimeout: int = 75,
			WindowWidth: int = 1920,
			WindowHeight: int = 1080
		):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Тип используемого браузера.
		self.BrowserType = BrowserType
		# Состояние: активен ли безрабочный режим.
		self.Headless = Headless
		# Тайм-аут загрузки страницы.
		self.PageLoadTimeout = PageLoadTimeout
		# Тайм-аут выполнения JavaScript.
		self.ScriptTimeout = ScriptTimeout
		# Ширина окна.
		self.WindowWidth = WindowWidth
		# Высота окна.
		self.WindowHeight = WindowHeight
		
	# Задаёт тип используемого браузера.
	def setBrowserType(self, BrowserType: Browsers):
		self.BrowserType = BrowserType
		
	# Переключает отображение окна браузера.
	def setHeadless(self, Headless: bool):
		self.Headless = Headless
		
	# Задаёт тайм-аут загрузки страницы.
	def setPageLoadTimeout(self, PageLoadTimeout: int):
		self.PageLoadTimeout = PageLoadTimeout
		
	# Задаёт тайм-аут выполнения JavaScript.
	def setScriptTimeout(self, ScriptTimeout: int):
		self.ScriptTimeout = ScriptTimeout
		
	# Задаёт размер окна браузера.
	def setWindowSize(self, Width: int, Height: int):
		self.WindowWidth = Width
		self.WindowHeight = Height
		
# Эмулятор структуры ответа библиотеки requests.
class WebResponse:
	
	#==========================================================================================#
	# >>>>> СТАТИЧЕСКИЕ СВОЙСТВА <<<<< #
	#==========================================================================================#
	# Статус ответа.
	status_code = None
	# Бинарное представление ответа.
	content = None
	# Текстовое представление ответа.
	text = None
	
	# Конструктор.
	def __init__(self):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Статус ответа.
		status_code = None
		# Бинарное представление ответа.
		content = None
		# Текстовое представление ответа.
		text = None
		
#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#
		
# Модуль для получение HTML кода веб-страниц.
class WebRequestor:
	
	# Возвращает состояние: задана ли конфигурация.
	def __CheckConfigPresence(self) -> bool:
		# Состояние: задана ли конфигурация.
		IsConfigSet = False if self.__Session == None and self.__Browser == None else True
		
		return IsConfigSet
	
	# Инициализация браузера Google Chrome.
	def __InitializeChrome(self):
		# Закрытие браузера.
		self.close()
		# Опции веб-браузера.
		ChromeOptions = Options()
		# Установка опций.
		ChromeOptions.add_argument("--no-sandbox")
		ChromeOptions.add_argument("--disable-dev-shm-usage")
		ChromeOptions.add_argument("--disable-gpu")
		ChromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])
		
		# При отключённом режиме отладки скрыть окно браузера.
		if self.__SeleniumConfig.Headless == True:
			ChromeOptions.add_argument("--headless=new")

		# Инициализация браузера.
		self.__Browser = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = ChromeOptions)
		# Установка размера окна браузера на FullHD для корректной работы сайтов.
		self.__Browser.set_window_size(self.__SeleniumConfig.WindowWidth, self.__SeleniumConfig.WindowHeight)
		# Установка максимального времени загрузки страницы и выполнения скрипта.
		self.__Browser.set_page_load_timeout(self.__SeleniumConfig.PageLoadTimeout)
		self.__Browser.set_script_timeout(self.__SeleniumConfig.ScriptTimeout)
		
	# Запрос страницы при помощи requests.
	def __GetByRequests(self, URL: str) -> WebResponse:
		# Ответ.
		Response = self.__Session.get(URL, headers = self.__RequestsConfig.Headers)
		
		return Response
	
	# Запрос страницы при помощи Selenium.
	def __GetBySelenium(self, URL: str) -> WebResponse:
		# Ответ.
		Response = WebResponse()
		
		try:
			# Запрос страницы.
			self.__Browser.get(URL)
			
		except TimeoutException:
			# Установка свойств ответа.
			Response.status_code = 408
			
		except Exception:
			# Установка свойств ответа.
			Response.status_code = 499
			
		else:
			# Установка свойств ответа.
			Response.status_code = 200
			Response.text = self.__Browser.execute_script("return document.body.innerHTML;")
			Response.content = bytes(Response.text)
		
		return Response
			
	# Конструктор.
	def __init__(self):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Конфигурация requests.
		self.__RequestsConfig = RequestsConfig()
		# Конфигурация Selenium.
		self.__SeleniumConfig = SeleniumConfig()
		# Сессия запросов.
		self.__Session = None
		# Состояние: используется ли Selenium.
		self.__IsSeleniumUsed = False
		# Экземпляр веб-браузера.
		self.__Browser = None
		
	# Закрывает модуль запросов.
	def close(self):
		
		# Если для запросов используется Selenium.
		if self.__IsSeleniumUsed == True:
			
			try:
				# Закрытие браузера.
				self.__Browser.close()
				self.__Browser.quit()
				# Обнуление экземпляра.
				self.__Browser = None
			
			except Exception:
				pass
			
		else:
			# Закрытие сессии.
			self.__Session.close()
			# Обнуление сессии.
			self.__Session = None
		
	# Выполняет JavaScript.
	def executeJavaScript(self, Script: str, Async: bool = False, TriesCount: int = 1) -> WebResponse:
		# Ответ.
		Response = WebResponse()
		
		# Если веб-драйвер инициализирован.
		if self.__Browser != None:
			# Результат выполнения скрипта.
			Result = None
			# Количество повторов.
			CurrentTry = 0
			# Состояние: вернул ли скрипт ответ.
			IsLoaded = False
		
			# Повторять, пока скрипт не вернёт ответ.
			while IsLoaded == False:
				
				try:
					# Выполнение скрипта и запись результата.
					Result = self.__Browser.execute_async_script(Script) if Async == True else self.__Browser.execute_script(Script)
				
				except TimeoutException:
					# Установка свойств ответа.
					Response.status_code = 408
					
				except Exception:
					# Инкремент количества повторов.
					CurrentTry += 1
					# Установка свойств ответа.
					Response.status_code = 400
					
					# Если достигнуто максимальное количество повторов, остановить повторные запросы.
					if CurrentTry == TriesCount:
						break
			
				else:
					# Переключение статуса выполнения скрипта.
					IsLoaded = True
					# Установка свойств ответа.
					Response.status_code = 200
					Response.text = Result
					Response.content = bytes(Result)
					
			else:
				# Выброс исключения.
				raise SeleniumRequired()
				
		return Response
		
	# Загружает страницу.
	def get(self, URL: str) -> WebResponse:
		# Ответ.
		Response = WebResponse()
		
		# Если задана конфигурация, то выполнить запрос.
		if self.__CheckConfigPresence() == True:
			Response = self.__GetBySelenium(URL) if self.__IsSeleniumUsed == True else self.__GetByRequests(URL)
			
		else:
			# Выброс исключения.
			raise ConfigRequired()
			
		return Response
	
	# Возвращает дескриптор экземпляра браузера.
	def getBrowserHandler(self) -> webdriver.Chrome | None:
		
		# Если веб-драйвер не инициализирован, выбросить исключение.
		if self.__Browser == None:
			raise SeleniumRequired()
		
		return self.__Browser
			
	# Задаёт конфигурацию и инициализирует модуль запросов.
	def initialize(self, Config: RequestsConfig | SeleniumConfig = RequestsConfig()):
		
		# Если задана конфигурация Selenium.
		if type(Config) == SeleniumConfig:
			# Переключение состояния Selenium.
			self.__IsSeleniumUsed = True
			# Сохранение конфигурации.
			self.__SeleniumConfig = Config
			
			# Инициализация выбранного браузера.
			match Config.BrowserType:
				case Browsers.Chrome:
					self.__InitializeChrome()
					
		# Если задана конфигурация requests.		
		elif type(Config) == RequestsConfig:
			# Переключение состояния Selenium.
			self.__IsSeleniumUsed = False
			# Сохранение конфигурации.
			self.__RequestsConfig = Config
			# Инициализация сессии.
			self.__Session = requests.Session()