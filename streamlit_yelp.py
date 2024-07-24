import subprocess
import json
import pandas as pd
import os
import requests
from streamlit_js_eval import streamlit_js_eval, copy_to_clipboard, create_share_link, get_geolocation
from utils import get_user_location, generate_unique_filename, file_exists, page, re
from geopy.geocoders import Nominatim
import streamlit as st
from PIL import Image
import uuid

st.set_page_config(
    layout="wide",
    page_title=page['title'],
    page_icon='assets/Scappy_Crawler.png',
)

st.title('Cyberoni LeadGen Scraper: Unleash Sales Potential With Python')
st.text(page['description'])
image = Image.open('assets/Scappy_Crawler.png')
st.image(image, caption='CyberOni Yelp Page Scraper')

# Initialize location variables
pulled_city = 'Denver'
pulled_state = 'CO'
pulled_zip_code = '80010'

geolocator = Nominatim(user_agent="YelpUserLocationID")


def display_results_and_links(json_file_path, csv_file_path):
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        with st.expander("View Results", expanded=False):
            st.json(data)
        with open(json_file_path, 'rb') as f:
            st.download_button(
                label="Download JSON",
                data=f,
                file_name=json_file_path,
                mime='application/json',
                key="JSON_DOWNLOAD_BUTTON" + str(uuid.uuid4())
            )
    else:
        st.error('No data found. Please run the function first.')

    if os.path.exists(csv_file_path):
        with open(csv_file_path, 'rb') as f_csv:
            st.download_button(
                label="Download CSV",
                data=f_csv,
                file_name=csv_file_path,
                mime='text/csv',
                key="CSV_DOWNLOAD_BUTTON" + str(uuid.uuid4())
            )
    else:
        st.warning('No CSV data found. Please run the function and generate CSV data.')


if 'returned_json_file_path' not in st.session_state:
    st.session_state['returned_json_file_path'] = "None"
if 'returned_csv_file_path' not in st.session_state:
    st.session_state['returned_csv_file_path'] = "None"

if st.session_state['returned_json_file_path'] != "None" and st.session_state['returned_csv_file_path'] != "None":
    display_results_and_links(
        st.session_state['returned_json_file_path'], st.session_state['returned_csv_file_path']
    )

with st.expander("Read Me"):
    st.markdown("""
        # Cyberoni Yelp Scrapy Spider - Read Me

        This Streamlit app allows you to run a Scrapy spider to scrape Yelp data based on your input parameters.

        ## Input Form
        - Fill in the search term, city, zip code, state, and maximum pages.
        - You can also choose to run the spider with unlimited pages.

        ## Running the Spider
        - Click the "Run Spider" button to start the spider with the provided parameters.
        - The spider will generate JSON and CSV files.

        ## Viewing Results
        - Go to the "Show Results" section to view the scraped data.
        - You can download the JSON and CSV files for further analysis.

        ## Troubleshooting
        - If you encounter any issues, try refreshing the page.
        - Make sure you have an internet connection and provide valid input.

        Thank you for using the Yelp Scrapy Spider app!
        👨🏾‍💻[GitHub Repository](https://github.com/techwithty)
        🏢[LinkedIN](https://linkedin.com/softwearu)
    """)

    try:
        user_agent = streamlit_js_eval(
            js_expressions='window.navigator.userAgent', want_output=True, key='UA')
        st.write(f"User agent is _{user_agent}_")
    except Exception as e:
        st.error(f"An error occurred while fetching user agent: {str(e)}")

    try:
        screen_width = streamlit_js_eval(
            js_expressions='screen.width', want_output=True, key='SCR')
        st.write(f"Screen width is _{screen_width}_")
    except Exception as e:
        st.error(f"An error occurred while fetching screen width: {str(e)}")

    try:
        browser_language = streamlit_js_eval(
            js_expressions='window.navigator.language', want_output=True, key='LANG')
        st.write(f"Browser language is _{browser_language}_")
    except Exception as e:
        st.error(f"An error occurred while fetching browser language: {str(e)}")

    try:
        page_location = streamlit_js_eval(
            js_expressions='window.location.origin', want_output=True, key='LOC')
        st.write(f"Page location is _{page_location}_")
    except Exception as e:
        st.error(f"An error occurred while fetching page location: {str(e)}")

    copy_to_clipboard("Text to be copied!", "Copy Github Link (only on HTTPS)",
                      "Successfully copied", component_key="CLPBRD")

    create_share_link(dict({'title': 'streamlit-js-eval', 'url': 'https://github.com/techwithty',
                            'text': "A description"}), "Share a URL (only on mobile devices)", 'Successfully shared', component_key='shdemo')

if st.checkbox("Check my location"):
    loc = get_geolocation()
    if loc:
        latitude = loc['coords']['latitude']
        longitude = loc['coords']['longitude']
        location = geolocator.reverse((latitude, longitude), exactly_one=True)

        if location:
            address_str = str(location)
            address_parts = address_str.split(',')
            pulled_city = address_parts[2].strip() if len(address_parts) > 2 else 'Unknown'
            pulled_state = address_parts[-3].strip() if len(address_parts) > 3 else 'Unknown'
            pulled_zip_code = address_parts[-2].strip() if len(address_parts) > 2 else 'Unknown'

            st.write(f"Your coordinates are {latitude}, {longitude}")
            st.write(f"Location: {pulled_city}, {pulled_state}, {pulled_zip_code}")
    else:
        st.write("Waiting for location...")

def run_scrapy_spider(search_term, city, zip_code, state, max_pages):
    missing_fields = []
    if not search_term:
        missing_fields.append('Search Term')
    if not city:
        missing_fields.append('City')
    if not zip_code:
        missing_fields.append('Zip Code')
    if not state:
        missing_fields.append('State')

    if missing_fields:
        error_message = "Please fill out the following required fields: " + ", ".join(missing_fields) + " ❌"
        st.error(error_message)
        return None, None

    file_name = generate_unique_filename(city, search_term)
    json_file_path = os.path.join("dumps", f"cleaned{file_name}.json")
    csv_file_path = os.path.join("dumps", f"{generate_unique_filename(city, search_term)}.csv")

    csv_exists = file_exists(csv_file_path)
    json_exists = file_exists(json_file_path)
    st.write(f"JSON File Exists: {json_exists}")
    st.write(f"CSV File Exists: {csv_exists}")

    st.session_state['returned_json_file_path'] = json_file_path
    st.session_state['returned_csv_file_path'] = csv_file_path

    try:
        command = [
            'scrapy', 'crawl', 'yelp-crawler',
            '-a', f'search={search_term}',
            '-a', f'city={city}',
            '-a', f'zip_code={zip_code}',
            '-a', f'state={state}',
            '-a', f'max_pages={max_pages}'
        ]
        if command:
            subprocess.run(command)
            st.success('Spider run completed!')
    except:
        st.write("Please input all Search term, City, Zip Code, State Fields ✅")

    return json_file_path, csv_file_path


toggle_sidebar = False

if not toggle_sidebar:
    selected_tab = st.sidebar.radio(
        "Choose a tab:", ["Input Form", "Show Results"]
    )

if toggle_sidebar or (selected_tab == "Input Form"):
    search_term = st.text_input('Search Term', 'fitness')
    city = st.text_input('City', pulled_city)
    zip_code = st.text_input('Zip Code', pulled_zip_code)
    state = st.text_input('State', pulled_state)
    use_unlimited_pages = st.checkbox('Unlimited Pages', value=False)

    if not use_unlimited_pages:
        max_pages = st.number_input('Max Pages', min_value=2, step=1, value=2)

    if st.button('Run Spider'):
        if use_unlimited_pages:
            max_pages = False
        run_scrapy_spider(search_term, city, zip_code, state, max_pages)

if st.button('Refresh'):
    st.experimental_rerun()

display_results_and_links(
    st.session_state['returned_json_file_path'], st.session_state['returned_csv_file_path']
)
