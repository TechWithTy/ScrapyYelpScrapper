import scrapy


class BusinessCrawlerSpider(scrapy.Spider):
    name = "business-crawler"
    allowed_domains = ["yelp.com"]
    start_urls = ["https://yelp.com"]

    def parse(self, response):
        pass
