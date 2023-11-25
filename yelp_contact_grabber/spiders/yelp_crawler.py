import scrapy
from pathlib import Path

class YelpCrawlerSpider(scrapy.Spider):
    name = "yelp-crawler"
    allowed_domains = ["yelp.com"]
    start_urls = ["https://yelp.com"]

    def start_requests(self):
        urls = [
            "https://quotes.toscrape.com/page/1/",
            "https://quotes.toscrape.com/page/2/",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
            page = response.url.split("/")[-2]
            filename = f"quotes-{page}.html"
            Path(filename).write_bytes(response.body)
            self.log(f"Saved file {filename}")
