# File: scraper/scraper/items.py
# COMPLETE REPLACEMENT

import scrapy


class StreamingItem(scrapy.Item):
    """Item for movies/shows with streaming links"""
    movie_pk = scrapy.Field()
    imdb_id = scrapy.Field()
    title = scrapy.Field()
    year = scrapy.Field()
    type = scrapy.Field()
    poster_url = scrapy.Field()
    synopsis = scrapy.Field()
    original_detail_url = scrapy.Field()
    links = scrapy.Field()  # List of dicts: [{quality, language, source_url}]


class MovieItem(scrapy.Item):
    """Legacy item for backward compatibility"""
    imdb_id = scrapy.Field()
    title = scrapy.Field()
    year = scrapy.Field()
    synopsis = scrapy.Field()
    poster_url = scrapy.Field()
    source_url = scrapy.Field()
    source_site = scrapy.Field()
    stream_url = scrapy.Field()
    server_name = scrapy.Field()
    quality = scrapy.Field()
    language = scrapy.Field()