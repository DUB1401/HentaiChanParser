from PIL import Image

import random
import time

# Возвращает разрешение изображения.
def GetImageResolution(Path: str) -> dict:
	# Разрешение.
	Resolution = {
		"width": None,
		"height": None
	}
	
	try:
		
		# Чтение изображения.
		with Image.open(Path) as ImageReader:
			
			# Если формат изображения *.JPEG.
			if ImageReader.format == "JPEG":
				# Запись разрешения.
				Resolution["width"] = ImageReader.size[0]
				Resolution["height"] = ImageReader.size[1]
				
	except: pass
	
	return Resolution

# Усекает число до определённого количества знаков после запятой.
def ToFixedFloat(FloatNumber: float, Digits: int = 0) -> float:
	return float(f"{FloatNumber:.{Digits}f}")

# Проевращает число секунд в строку-дескриптор времени по формату [<x> hours <y> minuts <z> seconds].
def SecondsToTimeString(Seconds: float) -> str:
	# Количество часов.
	Hours = int(Seconds / 3600.0)
	Seconds -= Hours * 3600
	# Количество минут.
	Minutes = int(Seconds / 60.0)
	Seconds -= Minutes * 60
	# Количество секунд.
	Seconds = ToFixedFloat(Seconds, 2)
	# Строка-дескриптор времени.
	TimeString = ""

	# Генерация строки.
	if Hours > 0:
		TimeString += str(Hours) + " hours "
	if Minutes > 0:
		TimeString += str(Minutes) + " minutes "
	if Seconds > 0:
		TimeString += str(Seconds) + " seconds"

	return TimeString

# Выжидает согласно заданному интервалу.
def Wait(Settings: dict):
	time.sleep(random.randint(Settings["min-delay"], Settings["max-delay"]))