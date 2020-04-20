# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrape.models import ScrapyModel
#from scrapy_djangoitem import DjangoItem


class BotsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class HotelItem(scrapy.Item):
    hotel_name = scrapy.Field()
    comm = scrapy.Field()
    source = scrapy.Field()
    label = scrapy.Field()
