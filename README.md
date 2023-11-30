# ScrappyYelpScraper

![Scrappy Crawler](https://i.postimg.cc/C12phFSG/Scappy-Crawler.png)

## Introduction

ScrappyYelpScraper is a Python-based tool designed to scrape and extract data from Yelp listings. This tool is ideal for gathering information such as business names, contact details, reviews, and ratings from Yelp, providing valuable insights for market analysis, customer feedback, and competitive research.

## Features

- **Data Extraction**: Extracts key details like business names, addresses, contact information, and user reviews from Yelp listings.
- **Filtering Options**: Allows users to specify search criteria such as location, business type, and ratings.
- **Export Functionality**: Supports exporting the scraped data into CSV or JSON formats for easy analysis and integration.

## Installation

To set up ScrappyYelpScraper, follow these steps:

1. Clone the repository:
   git clone [repository URL]

css
Copy code 2. Navigate to the project directory:
cd ScrappyYelpScraper

markdown
Copy code 3. Install the required dependencies:
pip install -r requirements.txt

arduino
Copy code

## Usage

To start using ScrappyYelpScraper, run the main script:

streamlit run streamlit_yelp.py

Python scrappy_yelp_scraper.py

To run via the cmd
scrapy crawl yelp-crawler -a search=[search_term] -a city=[city] -a zip_code=[zip_code] -a state=[state] -a max_pages=[max_pages]

scrapy crawl yelp-crawler -a search=restaurants -a city=New York -a zip_code=10001 -a state=NY -a max_pages=5

This will open a browser web interface, for the search terms needed

All Fields must be provided , we have included a script to input your location by pressing a button.

Once the script is done it will output a table and have both downloadable csv and json files.

_Note: Replace `scrappy_yelp_scraper.py` with the actual name of your main script._

## Odities

    Some Libraries have to be imported like this in requirments.txt
    -git+https://github.com/aghasemi/streamlit_js_eval#egg=streamlit_js_eval

    Pip freeze generates a file that causes a issue in streamlit

    -twisted-iocpsupport==1.0.4 (remove)

## Configuration

All Fields must be provided , we have included a script to input your location by pressing a button.

## Contributing

Contributions to ScrappyYelpScraper are welcome! Please read `CONTRIBUTING.md` for details on our code of conduct and the process for submitting pull requests to us.

## License

This project is licensed under the MIT License - see the `LICENSE.md` file for details.

## Acknowledgments

This project would not have been possible without the valuable contributions from various individuals and the use of open-source software. We extend our gratitude to the following:

### Contributors

- [List of individual contributors, if any]

### Third-Party Libraries

- **Scrapy**: A fundamental component of our web scraping functionality is powered by Scrapy, a high-level web crawling and scraping framework for Python. Scrapy is BSD-licensed, and we are grateful for the robust foundation it provides for our data extraction needs. The Scrapy framework is developed and maintained by the Scrapy community. For more information on the Scrapy license, please visit the [Scrapy GitHub repository](https://github.com/scrapy/scrapy).

- **Streamlit**: Our interactive data applications are made possible with the help of Streamlit, an open-source app framework for Machine Learning and Data Science teams. Streamlit is distributed under the Apache 2.0 license, and we appreciate its contribution to making our data visualizations more engaging and accessible. For details on Streamlit’s license, refer to the [Streamlit GitHub repository](https://github.com/streamlit/streamlit).

### Resources

- [Any other resources, libraries, or tools used in the project]
