import scrapy
import logging
from pathlib import Path
import json
import re
from urllib.parse import urlparse, parse_qs, urlunparse

# Define ANSI escape codes for blue text
BLUE_TEXT = "\033[94m"
END_COLOR = "\033[0m"

all_links = []
half_all_links = []
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
        self.data_list = []

        self.temp_links = []  # Temporary list to store links from each page

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
        try:  # Extract the href attribute of each link
            links = response.css(
                '[class*="businessName"] a::attr(href)').getall()
            self.temp_links.extend([self.generate_yelp_url(link)
                                    for link in links])

            # Append links to the global all_links variable
            all_links.extend(self.temp_links)
            
            next_page_url = response.css(
                'span.css-foyide a.next-link::attr(href)').get()
            # Generate full Yelp URLs from relative links
            full_urls = [self.generate_yelp_url(link) for link in links]

            # Follow All Links
            if next_page_url:
                # Yield a new request to scrape the next page
                yield scrapy.Request(next_page_url, self.parse)
            else:
                # No more pages, now extend all_links with the collected links
                all_links.extend(self.temp_links)

                # Check if there are links to follow

                # Clear the temp_links list
                self.temp_links = []

            # Output the links to a JSON file
            with open('yelp_links.json', 'w') as json_file:
                json.dump({'links': all_links}, json_file, indent=4)

            # for url in full_urls:
            #     print(url)
            print(f"{BLUE_TEXT}{len(all_links)}{END_COLOR}")
        except Exception as e:
            logging.error(f"Error occurred during parsing: {str(e)}")

        if all_links:
            yield from response.follow_all(all_links, self.parse_business_page)
        else:
            print("All Links Empty")
            return


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
        owner_name = response.xpath("//p[text()='Business owner information']/following-sibling::div//p/text()").get()
        business_review_highlights = response.xpath("//div[contains(@class, 'css-1hqozct')]//p/span/text()").getall()

    # Extracting the role of the person
        

        # Extracting review information
        # Using regular expressions to extract the rating and number of reviews
        review_info = response.css('div.arrange-unit__09f24__rqHTg span.css-1p9ibgf::text').getall()
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
        # Define a method that is called when the spider is closed
        if hasattr(self, 'data_list'):
            # Write the list of dictionaries to a JSON file
            with open('extracted_data.json', 'w') as json_file:
                json.dump(self.data_list, json_file, indent=4)

        super().closed(reason)