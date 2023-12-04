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
from scrapy_selenium import SeleniumRequest 

# Define ANSI escape codes for blue text
BLUE_TEXT = "\033[94m"
END_COLOR = "\033[0m"

# has to be greater than 1 as 1 is the starting number

all_links = []
half_all_links = []
# Get all links
# response.css(
#     "div.businessName__09f24__EYSZE h3.css-1agk4wl a::attr(href)").getall()
outputCsvFile = True


class YelpCrawlerPlaywrightSpider(scrapy.Spider):
    name = "yelp-selenium"
    allowed_domains = ["yelp.com"]
    start_urls = ["https://yelp.com"]

    custom_settings = {
        "LOG_LEVEL": "INFO",  # Set the log level to INFO
        'ROBOTSTXT_OBEY': False,

    }

    def __init__(self, *args, **kwargs):
        super(YelpCrawlerPlaywrightSpider, self).__init__(*args, **kwargs)
        self.data_list = []

        self.temp_links = []
        self.temp_links = []

        self.num_pages_visited = 0
        self.max_pages_to_visit = False  # Temporary list to store links from each page

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
        self.search_terms["max_pages"] = kwargs.get("max_pages")

    def start_requests(self):
        base_url = "https://www.yelp.com/search?"
        city = self.search_terms["city_search_term"] or "default_city"
        zip_code = self.search_terms["city_zip_search_term"] or "default_zip_code"
        state = self.search_terms["state"] or "default_state"
        search_term = self.search_terms["search_term"] or "default_search_term"

        try:
            # Check if all required variables are not None
            if self.search_terms:
                # Construct the URL with all variables and page number
                url = f"{base_url}find_loc={city}%2C+{state}+{zip_code}&find_desc={search_term.replace(' ', '+')}&start={self.page * 10}"
                # Print the URL in blue text
                print(f"{BLUE_TEXT}{url}{END_COLOR}")
                yield SeleniumRequest(url=url, callback=self.parse)
            else:
                logging.error("Missing required variables for crawling.")
        except Exception as e:
            logging.error(f"Error in start_requests: {str(e)}")

    def parse(self, response):
        try:
            # Extract the href attribute of each link
            links = response.css(
                '[class*="businessName"] a::attr(href)').getall()
            self.temp_links.extend(
                [self.generate_yelp_url(link) for link in links])
            all_links.extend(self.temp_links)

            next_page_url = response.css(
                'span.css-foyide a.next-link::attr(href)').get()

            # Increment the number of pages visited
            self.num_pages_visited += 1

            # Check if the maximum number of pages is reached
            if self.max_pages_to_visit and self.num_pages_visited >= self.max_pages_to_visit:
                print(
                    "\033[93mReached the maximum number of pages to visit.\033[0m")
                return  # Stop the spider
            elif next_page_url:
                # Yield a new request to scrape the next page
                yield SeleniumRequest(url=next_page_url, callback=self.parse)

            # Output the links to a JSON file
            with open(os.path.join("dumps", "yelp_links.json"), 'w') as json_file:

                json.dump({'links': all_links}, json_file, indent=4)

            print(f"{BLUE_TEXT}{len(all_links)}{END_COLOR}")

            if all_links:
                business_data = []
                for link in all_links:
                    business_data.append(SeleniumRequest(
                        url=link, callback=self.parse_business_page))

                yield from business_data
            else:
                print("All Links Empty")

        except Exception as e:
            logging.error(f"Error occurred during parsing: {str(e)}")

    def generate_yelp_url(self, path):
        base_url = "https://www.yelp.com"
        return base_url + path

    def parse_business_page(self, response):
        # Process each individual business page
        # Example: Extract specific details from the business page
        # business_details = ...
        # yield business_details
        # Extracting the business website
        # Looking for a text node 'Business website' and then navigating to the <a> tag

        current_url = response.url

        # Parse the URL to extract query parameters
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)

        # Extract the "osq" query parameter (search query)
        search_query = query_params.get('osq', [''])[0]

        # Extract the path (business name) from the URL
        path_parts = parsed_url.path.split('/')
        business_name = path_parts[-1] if path_parts[-1] else path_parts[-2]

        # Replace hyphens with spaces and capitalize the first letter of each word
        business_name = re.sub(r'-', ' ', business_name).title()
        business_website = response.xpath(
            "//p[text()='Business website']/following-sibling::p/a/text()").get()
        business_yelp_website = current_url

        # Extracting the phone number
        # Looking for a text node 'Phone number' and then extracting the phone number
        phone_number = response.xpath(
            "//p[text()='Phone number']/following-sibling::p/text()").get()
        owner_name = response.xpath(
            "//p[text()='Business owner information']/following-sibling::div//p/text()").get()
        business_review_highlights = response.xpath(
            "//div[contains(@class, 'css-1hqozct')]//p/span/text()").getall()

    # Extracting the role of the person

        # Extracting review information
        # Using regular expressions to extract the rating and number of reviews
        review_info = response.css(
            'div.arrange-unit__09f24__rqHTg span.css-1p9ibgf::text').getall()
        review_rating = next((re.findall(r"\d+\.\d+", info)
                             for info in review_info if re.search(r"\d+\.\d+", info)), None)
        number_of_reviews = next((re.findall(r"\d+ reviews", info)
                                 for info in review_info if re.search(r"\d+ reviews", info)), None)

        # Extracting the business category
        # Using broader CSS selectors and text content to identify the category
        business_category = response.css('span.css-1xfc281 a::text').getall()

        extracted_data = {
            'owner_name': owner_name,
            'business_name': business_name,

            'business_website': business_website,
            'yelp_website': business_yelp_website,
            'phone_number': phone_number,
            'review_rating': review_rating,
            'number_of_reviews': number_of_reviews,
            'business_categories': business_category,
        }

        self.data_list.append(extracted_data)
        # Yielding the data
        yield extracted_data

        # Printing the data for demonstration
        print("Extracted Data:", extracted_data)
        print(f"Visited {response.url}")
        # For demonstration, just printing the URL
        print(f"Visited {response.url}")

    def closed(self, reason):
        # Generate a unique filename in the "dumps" folder
        filename = generate_unique_filename(
            self.search_terms["city_search_term"],
            self.search_terms["search_term"],

        )

        # Write the extracted data to a JSON file in the "dumps" folder
        if hasattr(self, 'data_list'):
            with open(os.path.join("dumps", filename + ".json"), 'w') as file:
                json.dump(self.data_list, file, indent=4)

        try:
            cleaned_data = clean_json_data(self.data_list)

            # Write the cleaned data to a JSON file in the "dumps" folder
            with open(os.path.join("dumps", "cleaned" + filename + ".json"), 'w') as file:
                json.dump(cleaned_data, file, indent=4)
        except Exception as e:
            print('Cleaning failed:', e)
            return

        if outputCsvFile:
            # Convert cleaned data to a DataFrame
            df = pd.DataFrame(cleaned_data)

            # Save data to CSV in the "dumps" folder
            df.to_csv(os.path.join("dumps", filename + ".csv"), index=False)
