from selenium import webdriver
from threading import Timer
from time import sleep

import logging

class BrowserNavigator:
	
	# Останавливает загрузку страницы.
	def __StopLoading(self):

		# Если страница не загружена, то остановить загрузку.
		if self.__IsLoaded == False:
			self.__Browser.execute_script("window.stop();")

		# Запись в лог ошибки: загрузка страницы прервана.
		logging.debug("Page loading timed out. Stopped.")

	# Конструктор: задаёт глобальные настройки и экземпляр браузера.
	def __init__(self, Settings: dict, Browser: webdriver.Chrome):

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Состояние: загружена ли страница.
		self.__IsLoaded = None
		# Экземпляр браузера.
		self.__Browser = Browser

	# Возвращает HTML код тела страницы после полной загрузки.
	def GetBodyHTML(self) -> str:
		# HTML код тела страницы после полной загрузки.
		BodyHTML = str(self.__Browser.execute_script("return document.body.innerHTML;"))

		return BodyHTML

	# Выполняет переход на указанную страницу.
	def LoadPage(self, URL: str, Timeout: int = 0):
		# Состояние: выполняются ли условия перехода по URL.
		LoadCondition = True
		# Таймер ожидания загрузки.
		StopTimer = Timer(Timeout, self.__StopLoading)

		# Установка состояния загрузки.
		if Timeout == 0:
			self.__IsLoaded = None
		else:
			self.__IsLoaded = False

		# Проверка условия перехода: браузер находится на той же странице.
		if self.__Browser.current_url == URL:
			LoadCondition = False

		# Проверка условия перехода: сдвиг равен нуля и браузер находится на той же странице.
		if self.__Browser.current_url == URL.replace("?offset=0", ""):
			LoadCondition = False

		# Если все условия выполнены.
		if LoadCondition == True:
			# Состояние: успешна ли загрузка страницы.
			IsLoaded = False
			# Количество повторов.
			TriesCount = 0
			
			# Если установлен тайм-аут, то запустить таймер остановки загрузки страницы.
			if Timeout > 0:
				StopTimer.start()

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
					
					# Если достигнуто максимальное количество повторов, выбросить исключение.
					if TriesCount == self.__Settings["retry-tries"]:
						raise TimeoutError("unable to load page")

					# Выжидание интервала повтора.
					sleep(self.__Settings["retry-delay"])
			
				else:
					# Переключение статуса загрузки страницы.
					IsLoaded = True
					# Остановка таймера.
					StopTimer.cancel()