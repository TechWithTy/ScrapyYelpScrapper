import scrapy
import logging
from pathlib import Path
import json
import re
from urllib.parse import urlparse, parse_qs, urlunparse
import pandas as pd
from utils import clean_json_data, generate_unique_filename, random_uuid
import streamlit as st
import os

# Define ANSI escape codes for blue text
BLUE_TEXT = "\033[94m"
END_COLOR = "\033[0m"

# Selectors dictionary
SELECTORS = {
    "links": '[class*="businessName"] a::attr(href)',
    "next_page": 'span.css-foyide a.next-link::attr(href)',
    "business_website": "//p[text()='Business website']/following-sibling::p/a/text()",
    "phone_number": "//p[text()='Phone number']/following-sibling::p/text()",
    "owner_name": '//section[@aria-label="About the Business"]//p[@data-font-weight="bold"]/text()',
    "reviews": '//ul[contains(@class, "list__")]/li',
    "user_name": './/div[@role="region"]/@aria-label',
    "user_location": './/div[@data-testid="UserPassportInfoTextContainer"]//span/text()',
    "review_date": './/div[contains(@class, "arrange-unit-fill")]//span/text()',
    "review_text": './/p[contains(@class, "comment__")]/span[contains(@class, "raw__")]/text()',
    "rating": './/div[contains(@aria-label, "star rating")]/@aria-label',
    "reactions": './/div[@role="button"]/@aria-label',
    "owner_reply": './/div[@class="margin-t3__373c0__1l90z padding-t3__373c0__2cfJV border--top__373c0__3gXLy"]',
    "owner_reply_name": './/p[contains(@class, "css-1agk4wl")]/text()',
    "owner_reply_date": './/span[@class="css-e81eai"]/text()',
    "owner_reply_text": './/span[@class="raw__373c0__3rcx7"]/text()',
    "review_rating": '/html/body/yelp-react-root/div[1]/div[6]/div/div[1]/div[1]/main/div[3]/div/section/div[2]/div[3]/div/div[1]/div/span/div[2]/p',
    "number_of_reviews": '//div[contains(@class, "arrange-unit__09f24__rqHTg")]//span[contains(@class, "y-css-t1npoe")]/a/text()',
    "business_categories": '//span[contains(@class, "y-css-1o34y7f")]/a/text()',
    "google_maps_url": '//a[@href]/@href[contains(., "maps.googleapis.com/maps/api/staticmap")]/@href',
    "address": '//address//text()',
    "hours_rows": '//table[contains(@class, "hours-table__09f24__KR8wh")]//tr',
    "work_hours_day": './/th/p/text()',
    "work_hours_hours": './/td/ul/li/p/text()',
    "services_offered": '//section[@aria-label="Services Offered"]//p[contains(@class, "y-css-t1npoe")]/text()',
    "amenities": '//section[@aria-label="Amenities and More"]//div[contains(@class, "arrange-unit-fill")]//span[contains(@class, "y-css-1o34y7f")]/text()',
    "review_highlights_elements": '//section[@aria-label="Review Highlights"]//div[contains(@class, "arrange-unit-fill")]//p[contains(@class, "y-css-1s3mozr")]'
}

# Other constants
outputCsvFile = True
all_links = []

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
        self.data_list = []
        self.temp_links = []
        self.num_pages_visited = 0
        self.max_pages_to_visit = int(kwargs.get("max_pages", 0))  # Ensure this is an integer
        self.search_terms = {
            "search_term": kwargs.get("search", "fitness"),
            "city_search_term": kwargs.get("city", "Denver"),
            "city_zip_search_term": kwargs.get("zip_code", "80020"),
            "state": kwargs.get("state", "co"),
        }
        self.page = 0  # Default page number

    def start_requests(self):
        base_url = "https://www.yelp.com/search?"
        city = self.search_terms["city_search_term"]
        zip_code = self.search_terms["city_zip_search_term"]
        state = self.search_terms["state"]
        search_term = self.search_terms["search_term"]

        try:
            if self.search_terms:
                url = f"{base_url}find_loc={city}%2C+{state}+{zip_code}&find_desc={search_term.replace(' ', '+')}&start={self.page * 10}"
                print(f"{BLUE_TEXT}{url}{END_COLOR}")
                yield scrapy.Request(url, self.parse)
            else:
                logging.error("Missing required variables for crawling.")
        except Exception as e:
            logging.error(f"Error in start_requests: {str(e)}")

    def parse(self, response):
        try:
            links = response.css(SELECTORS["links"]).getall()
            self.temp_links.extend([self.generate_yelp_url(link) for link in links])
            all_links.extend(self.temp_links)

            next_page_url = response.css(SELECTORS["next_page"]).get()
            self.num_pages_visited += 1

            if self.max_pages_to_visit > 0 and self.num_pages_visited >= self.max_pages_to_visit:
                print("\033[93mReached the maximum number of pages to visit.\033[0m")
                return
            elif next_page_url:
                yield scrapy.Request(next_page_url, self.parse)

            with open(os.path.join("dumps", "yelp_links.json"), 'w') as json_file:
                json.dump({'links': all_links}, json_file, indent=4)

            print(f"{BLUE_TEXT}{len(all_links)}{END_COLOR}")

            if all_links:
                yield from response.follow_all(all_links, self.parse_business_page)
            else:
                print("All Links Empty")
        except Exception as e:
            logging.error(f"Error occurred during parsing: {str(e)}")

    def generate_yelp_url(self, path):
        base_url = "https://www.yelp.com"
        return base_url + path

    def parse_business_page(self, response):
        current_url = response.url
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)
        search_query = query_params.get('osq', [''])[0]
        path_parts = parsed_url.path.split('/')
        business_name = path_parts[-1] if path_parts[-1] else path_parts[-2]
        business_name = re.sub(r'-', ' ', business_name).title()
        business_website = response.xpath(SELECTORS["business_website"]).get()
        business_yelp_website = current_url
        phone_number = response.xpath(SELECTORS["phone_number"]).get()
        owner_name = response.xpath(SELECTORS["owner_name"]).get()
        reviews = response.xpath(SELECTORS["reviews"])
        extracted_reviews = []

        for review in reviews:
            user_name = review.xpath(SELECTORS["user_name"]).get()
            user_location = review.xpath(SELECTORS["user_location"]).get()
            review_date = review.xpath(SELECTORS["review_date"]).re_first(r'\w+ \d{1,2}, \d{4}')
            review_text = review.xpath(SELECTORS["review_text"]).get()
            rating = review.xpath(SELECTORS["rating"]).get()
            reactions = review.xpath(SELECTORS["reactions"]).extract()
            reactions_dict = {reaction.split(' (')[0]: int(reaction.split(' (')[1].rstrip(' reactions)').strip()) for reaction in reactions}

            def convert_rating(rating_text):
                if rating_text:
                    try:
                        return int(rating_text.split()[0])
                    except (ValueError, IndexError):
                        return None
                return None

            review_data = {
                'user_name': user_name,
                'user_location': user_location,
                'review_date': review_date,
                'rating': convert_rating(rating),
                'review_text': review_text,
                'reactions': reactions_dict
            }

            owner_reply = review.xpath(SELECTORS["owner_reply"])
            if owner_reply:
                owner_reply_name = owner_reply.xpath(SELECTORS["owner_reply_name"]).get()
                owner_reply_date = owner_reply.xpath(SELECTORS["owner_reply_date"]).get()
                owner_reply_text = owner_reply.xpath(SELECTORS["owner_reply_text"]).get()
                review_data['owner_reply'] = {
                    'owner_name': owner_reply_name,
                    'owner_reply_date': owner_reply_date,
                    'owner_reply_text': owner_reply_text,
                }

            extracted_reviews.append(review_data)

        review_rating_text = response.xpath(SELECTORS["review_rating"]).get()
        review_rating = float(review_rating_text) if review_rating_text and re.match(r'^\d+(\.\d+)?$', review_rating_text) else None
        number_of_reviews_text = response.xpath(SELECTORS["number_of_reviews"]).get()
        number_of_reviews = int(re.findall(r'\d+', number_of_reviews_text)[0]) if number_of_reviews_text else None
        business_categories = response.xpath(SELECTORS["business_categories"]).getall()
        work_hours = []

        try:
            google_maps_url = response.xpath(SELECTORS["google_maps_url"]).get()
            address = ' '.join(response.xpath(SELECTORS["address"]).extract()).strip()
            hours_rows = response.xpath(SELECTORS["hours_rows"])
            for row in hours_rows:
                day = row.xpath(SELECTORS["work_hours_day"]).get()
                hours = row.xpath(SELECTORS["work_hours_hours"]).get()
                if day and hours:
                    work_hours.append(f"{day}: {hours}")
        except Exception as e:
            self.logger.error(f"Error extracting Google Maps URL, address, or work hours: {e}")

        ratings = [review['rating'] for review in extracted_reviews if review['rating'] is not None]
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        filtered_reviews = [
                    review for review in extracted_reviews
                    if review['user_name'] is not None or
                    review['user_location'] is not None or
                    review['review_date'] is not None or
                    review['rating'] is not None or
                    review['review_text'] is not None or
                    review['reactions']
                ]
        services_offered = response.xpath(SELECTORS["services_offered"]).extract()
        amenities = response.xpath(SELECTORS["amenities"]).extract()
        review_highlights_elements = response.xpath(SELECTORS["review_highlights_elements"])
        review_highlights = [''.join(element.xpath('.//text()').extract()).strip() for element in review_highlights_elements]

        extracted_data = {
            'owner_name': owner_name,
            'business_name': business_name,
            'business_address': address,
            'business_website': business_website,
            'services_offered': services_offered,
            'amenities': amenities,
            'yelp_website': business_yelp_website,
            'phone_number': phone_number,
            'review_rating': average_rating,
            'number_of_reviews': len(filtered_reviews),
            'reviews': filtered_reviews,
            'review_highlights': review_highlights,
            'business_categories': business_categories,
            'address': address,
            'work_hours': work_hours,
        }

        self.data_list.append(extracted_data)
        yield extracted_data
        print("Extracted Data:", extracted_data)
        print(f"Visited {response.url}")

    def closed(self, reason):
        filename = generate_unique_filename(self.search_terms["city_search_term"], self.search_terms["search_term"])
        if hasattr(self, 'data_list'):
            with open(os.path.join("dumps", filename + ".json"), 'w') as file:
                json.dump(self.data_list, file, indent=4)

        try:
            cleaned_data = clean_json_data(self.data_list)
            with open(os.path.join("dumps", "cleaned" + filename + ".json"), 'w') as file:
                json.dump(cleaned_data, file, indent=4)
        except Exception as e:
            print('Cleaning failed:', e)
            return

        if outputCsvFile:
            df = pd.DataFrame(cleaned_data)
            df.to_csv(os.path.join("dumps", filename + ".csv"), index=False)
