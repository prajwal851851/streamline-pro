import scrapy


class StreamingItem(scrapy.Item):
    imdb_id = scrapy.Field()
    title = scrapy.Field()
    year = scrapy.Field()
    type = scrapy.Field()
    poster_url = scrapy.Field()
    synopsis = scrapy.Field()
    original_detail_url = scrapy.Field()  # Original source URL from 1flix.to
    links = scrapy.Field()  # Expect list of dicts: [{quality, language, source_url}]

