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

# has to be greater than 1 as 1 is the starting number

all_links = []
half_all_links = []
# Get all links
# response.css(
#     "div.businessName__09f24__EYSZE h3.css-1agk4wl a::attr(href)").getall()
outputCsvFile = True


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
                yield scrapy.Request(next_page_url, self.parse)

            # Output the links to a JSON file
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
        reviews = response.xpath('//li[contains(@class, "y-css-1jp2syp")]')
        extracted_reviews = []

        for review in reviews:
            user_name = review.xpath(
                './/span[@class="fs-block css-m6anxm"]/text()').get()
            user_location = review.xpath(
                './/span[@class="css-n6i4z7"]/text()').get()
            review_date = review.xpath(
                './/span[@class="css-e81eai"]/text()').get()
            review_text = review.xpath(
                './/span[@class="raw__373c0__3rcx7"]/text()').get()
            rating = review.xpath(
                './/div[contains(@aria-label, "star rating")]/@aria-label').get()

            review_data = {
                'user_name': user_name,
                'user_location': user_location,
                'review_date': review_date,
                'rating': rating,
                'review_text': review_text,
            }

            owner_reply = review.xpath(
                './/div[@class="margin-t3__373c0__1l90z padding-t3__373c0__2cfJV border--top__373c0__3gXLy"]')
            if owner_reply:
                owner_reply_name = owner_reply.xpath(
                    './/p[contains(@class, "css-1agk4wl")]/text()').get()
                owner_reply_date = owner_reply.xpath(
                    './/span[@class="css-e81eai"]/text()').get()
                owner_reply_text = owner_reply.xpath(
                    './/span[@class="raw__373c0__3rcx7"]/text()').get()

                review_data['owner_reply'] = {
                    'owner_name': owner_reply_name,
                    'owner_reply_date': owner_reply_date,
                    'owner_reply_text': owner_reply_text,
                }

            extracted_reviews.append(review_data)

    # Extracting the role of the person

        # Extracting review information
        # Using regular expressions to extract the rating and number of reviews
        review_rating_text = response.xpath(
            '/html/body/yelp-react-root/div[1]/div[6]/div/div[1]/div[1]/main/div[3]/div/section/div[2]/div[3]/div/div[1]/div/span/div[2]/p').get()
        review_rating = None

        if review_rating_text and re.match(r'^\d+(\.\d+)?$', review_rating_text):
            review_rating = float(review_rating_text)

        # Extract number of reviews
        number_of_reviews_text = response.xpath(
            '//div[contains(@class, "arrange-unit__09f24__rqHTg")]//span[contains(@class, "y-css-t1npoe")]/a/text()').get()
        number_of_reviews = int(re.findall(
            r'\d+', number_of_reviews_text)[0]) if number_of_reviews_text else None

        # Extracting the business category
        # Using broader CSS selectors and text content to identify the category
        business_categories = response.xpath(
            '//span[contains(@class, "y-css-1o34y7f")]/a/text()').getall()
        reviews_string = "\n".join([f"User: {review['user_name']}, Location: {review['user_location']}, Date: {review['review_date']}, Rating: {review['rating']}, Review: {review['review_text']}" +
                                    (f", Reply from {review['owner_reply']['owner_name']} on {review['owner_reply']['owner_reply_date']}: {
                                     review['owner_reply']['owner_reply_text']}" if 'owner_reply' in review else "")
                                    for review in extracted_reviews])

        google_maps_url = None
        address = None
        work_hours = []

        try:
            google_maps_url = response.xpath(
                '//a[@href]/@href[contains(., "maps.googleapis.com/maps/api/staticmap")]/@href').get()
            address = ' '.join(response.xpath(
                '//address//text()').extract()).strip()
            hours_rows = response.xpath(
                '//table[contains(@class, "hours-table__09f24__KR8wh")]//tr')
            for row in hours_rows:
                day = row.xpath('.//th/p/text()').get()
                hours = row.xpath('.//td/ul/li/p/text()').get()
                if day and hours:
                    work_hours.append(f"{day}: {hours}")
        except Exception as e:
            self.logger.error(
                f"Error extracting Google Maps URL, address, or work hours: {e}")

        def convert_rating(rating_text):
            return int(rating_text.split()[0])

        ratings = []
        for review in reviews:
            # Extract the rating text for each review
            # Adjust the CSS selector as needed
            rating_text = review.css('.rating::text').get()
            if rating_text:
                ratings.append(convert_rating(rating_text))

        average_rating = sum(ratings) / len(ratings) if ratings else 0

        extracted_data = {
            'owner_name': response.css('.owner-name::text').get(),
            'business_name': response.css('.business-name::text').get(),
            'business_website': response.css('.business-website::text').get(),
            'yelp_website': response.url,
            'phone_number': response.css('.phone-number::text').get(),
            'review_rating': average_rating,
            'number_of_reviews': number_of_reviews,
            'business_categories': response.css('.business-categories::text').getall(),
            # Adjust as needed
            'reviews': [{'rating': rating} for rating in ratings],
            'address': response.css('.address::text').get(),
            'work_hours': response.css('.work-hours::text').get(),
        }
        extracted_data = {
            'owner_name': owner_name,
            'business_name': business_name,

            'business_website': business_website,
            'yelp_website': business_yelp_website,
            'phone_number': phone_number,
            'review_rating':  average_rating,
            'number_of_reviews': len(extracted_reviews),
            'business_categories': business_categories,
            'reviews': extracted_reviews,
            'address': address,
            'work_hours': work_hours,

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
