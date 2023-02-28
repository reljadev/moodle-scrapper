# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrappingItem(scrapy.Item):
    file_urls = scrapy.Field()
    files = scrapy.Field()
    course_title = scrapy.Field()
    week_title = scrapy.Field()
    file_name = scrapy.Field()
