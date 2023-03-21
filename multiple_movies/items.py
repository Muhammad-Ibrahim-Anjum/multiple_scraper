# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MultipleMoviesItem(scrapy.Item):
    id = scrapy.Field()
    streaming_source = scrapy.Field()
    imdb_id = scrapy.Field()
    name = scrapy.Field()
    year = scrapy.Field()
    rating = scrapy.Field()
    imdb_rating = scrapy.Field()
    popularity = scrapy.Field()
    summary = scrapy.Field()
    length = scrapy.Field()
    genres = scrapy.Field()
    directors = scrapy.Field()
    actors = scrapy.Field()
    supporting_actors = scrapy.Field()
    producers = scrapy.Field()
    writers = scrapy.Field()
    studio = scrapy.Field()
    pg_rating = scrapy.Field()
    content_advisory = scrapy.Field()
    seasons = scrapy.Field()
    episodes = scrapy.Field()
    web_link = scrapy.Field()
    ios_link = scrapy.Field()
    android_link = scrapy.Field()
    trailer_url = scrapy.Field()
    poster_url = scrapy.Field()
    backdrop_url = scrapy.Field()
