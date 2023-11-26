import scrapy
import logging
from pathlib import Path
import json

# Define ANSI escape codes for blue text
BLUE_TEXT = "\033[94m"
END_COLOR = "\033[0m"

all_links = []
# Get all links
# response.css(
#     "div.businessName__09f24__EYSZE h3.css-1agk4wl a::attr(href)").getall()

class YelpCrawlerSpider(scrapy.Spider):
    name = "yelp-crawler"
    allowed_domains = ["yelp.com"]
    start_urls = ["https://yelp.com"]

    custom_settings = {
        "LOG_LEVEL": "INFO",  # Set the log level to INFO
        'ROBOTSTXT_OBEY': False,

    }

    def __init__(self, *args, **kwargs):
        super(YelpCrawlerSpider, self).__init__(*args, **kwargs)
        self.search_terms = {
            "search_term": "fitness",
            "city_search_term": "Denver",
            "city_zip_search_term": "80020",
            "state": "co"
        }
        self.page = 0  # Default page number

        # Access command-line arguments and assign them to instance variables
        self.search_terms["search_term"] = kwargs.get("search")
        self.search_terms["city_search_term"] = kwargs.get("city")
        self.search_terms["city_zip_search_term"] = kwargs.get("zip_code")
        self.search_terms["state"] = kwargs.get("state")

    def start_requests(self):
        base_url = "https://www.yelp.com/search?"
        city = "Denver"
        zip_code = "80020"
        state = "co"
        search_term = "fitness"
        try:
            # Check if all required variables are not None
            if all([city, zip_code, search_term, state]):
                # Construct the URL with all variables and page number
                url = f"{base_url}find_loc={city}%2C+{state}+{zip_code}&find_desc={
                    search_term.replace(' ', '+')}&start={self.page * 10}"
                # Print the URL in blue text
                print(f"{BLUE_TEXT}{url}{END_COLOR}")
                yield scrapy.Request(url, self.parse)
            else:
                logging.error("Missing required variables for crawling.")
        except Exception as e:
            logging.error(f"Error in start_requests: {str(e)}")


    def parse(self, response):
        # Extract the href attribute of each link
        links = response.css('[class*="businessName"] a::attr(href)').getall()

        # Append links to the global all_links variable
        all_links.extend(links)

        # Generate full Yelp URLs from relative links
        full_urls = [self.generate_yelp_url(link) for link in links]

        # Output the links to a JSON file
        with open('yelp_links.json', 'w') as json_file:
            json.dump({'links': full_urls}, json_file, indent=4)

        for url in full_urls:
            print(url)

    def generate_yelp_url(self, path):
        base_url = "https://www.yelp.com"
        return base_url + path
