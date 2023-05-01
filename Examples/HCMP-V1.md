# HCMP-V1
**HCMP-V1** – это формат для частичной совместимости с устаревшими форматами парсера сайта [Remanga](https://remanga.org/).

# Основные принципы
* _**Авторы без переводчиков**_ – переводчики не определяются, в отличие от авторов.
* _**Индекс от нуля**_ – индексация глав начинается с нуля.
* _**Ключи в camelCase**_ – для наименования ключей используются только латинские символы в camelCase.
* _**Модифицируемые теги**_ – ID тегов не определяется, а сами названия тегов могут быть изменены или переопределены в жанры.
* _**Неопределённая типизация**_ – все тайтлы на сайте [HentaiChan](https://hentaichan.live/) считаются типом _MANGA_.
* _**Неопределённые статусы**_ – все тайтлы на сайте [HentaiChan](https://hentaichan.live/) имеют статус _NOT_FOUND_.
* _**Только важные сведения**_ – формат содержит лишь ту информацию, что необходима для загрузки тайтла и его правильной обработки устаревшими импортёрами.

# Пример

```json
{
	"format": "hcmp-v1",
	"site": "hentaichan.live",
	"id": 123,
	"slug": "manga-name",
	"originalLink": "https://hentaichan.live/manga/123-manga-name.html",
	"fullTitle": null,
	"rusTitle": "Название манги",
	"engTitle": "Manga name",
	"alternativeTitle": "漫画名 / Mangamei",
	"type": "MANGA",
	"status": "NOT_FOUND",
	"isHentai": true,
	"isYaoi": false,
	"img": {
		"high": "manga-name/file.jpg",
		"mid": null,
		"low": null
	},
	"series": [
		{
			"id": 0,
			"name": "Название серии"
		}
	],
	"authors": [
		{
			"id": 0,
			"name": "Никнейм автора"
		}
	],
	"translators": [],
	"tags": [
		{
			"id": 0,
			"name": "Название тега"
		}
	],
	"genres": [
		{
			"id": 0,
			"name": "Название жанра"
		}
	],
	"chapters": [
		{
			"id": 10,
			"chapter": 1,
			"title": "",
			"tom": 1,
			"index": 0,
			"slides": [
				{
					"link": "https://link_to_slide/01.webp",
					"width": 720,
					"height": 1280
				}
			]
		}
	]
}
```

# Примечания
1. Другие названия тайтла отделяются сочетанием символов ` / ` (пробел-слеш-пробел).