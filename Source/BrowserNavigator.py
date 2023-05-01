from selenium import webdriver

class BrowserNavigator:

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Глобальные настройки.
	__Settings = dict()
	# Экземпляр браузера.
	__Browser = None

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#
	
	# Конструктор: задаёт глобальные настройки и экземпляр браузера.
	def __init__(self, Settings: dict, Browser: webdriver.Chrome):

		#---> Генерация свойств.
		#==========================================================================================#
		self.__Settings = Settings
		self.__Browser = Browser

	# Возвращает HTML код тела страницы после полной загрузки.
	def GetBodyHTML(self) -> str:
		# HTML код тела страницы после полной загрузки.
		BodyHTML = str(self.__Browser.execute_script("return document.body.innerHTML;"))

		return BodyHTML

	# Выполняет переход на указанную страницу.
	def LoadPage(self, URL: str):
		# Состояние: выполняются ли условия перехода по URL.
		LoadCondition = True

		# Проверка условия перехода: браузер находится на той же странице.
		if self.__Browser.current_url == URL:
			LoadCondition = False

		# Проверка условия перехода: сдвиг равен нуля и браузер находится на той же странице.
		if self.__Browser.current_url == URL.replace("?offset=0", ""):
			LoadCondition = False

		# Перейти на страницу если все условия выполнены.
		if LoadCondition == True:
			self.__Browser.get(URL)