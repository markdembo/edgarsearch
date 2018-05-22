import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from spider import HockeySpider

settings = get_project_settings()
settings.set("FEED_FORMAT", "csv")
settings.set("FEED_URI", "data.csv")
settings.set("LOG_LEVEL", "WARNING")
crawler = CrawlerProcess(settings)
crawler.crawl(HockeySpider)
crawler.start()
