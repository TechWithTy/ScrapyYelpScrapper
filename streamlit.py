import streamlit as st
import subprocess
import json
import pandas as pd
import os
import requests
# Function to trigger Scrapy spider
from streamlit_js_eval import streamlit_js_eval, copy_to_clipboard, create_share_link, get_geolocation
from utils import get_user_location, generate_unique_filename, file_exists
from geopy.geocoders import Nominatim


if 'returned_json_file_path' not in st.session_state:
    st.session_state['returned_json_file_path'] = "None"
if 'returned_csv_file_path' not in st.session_state:
    st.session_state['returned_csv_file_path'] = "None"


toggle_sidebar = st.button("Toggle Sidebar")

geolocator = Nominatim(user_agent="YelpUserLocationID")

loc = 0, 0

st.write(f"User agent is _{streamlit_js_eval(
    js_expressions='window.navigator.userAgent', want_output=True, key='UA')}_")

st.write(f"Screen width is _{streamlit_js_eval(
    js_expressions='screen.width', want_output=True, key='SCR')}_")

st.write(f"Browser language is _{streamlit_js_eval(
    js_expressions='window.navigator.language', want_output=True, key='LANG')}_")

st.write(f"Page location is _{streamlit_js_eval(
    js_expressions='window.location.origin', want_output=True, key='LOC')}_")

# Copying to clipboard only works with a HTTP connection

copy_to_clipboard("Text to be copied!", "Copy something to clipboard (only on HTTPS)",
                  "Successfully copied", component_key="CLPBRD")

# Share something using the sharing API
create_share_link(dict({'title': 'streamlit-js-eval', 'url': 'https://github.com/aghasemi/streamlit_js_eval',
                  'text': "A description"}), "Share a URL (only on mobile devices)", 'Successfully shared', component_key='shdemo')

pulled_city = None
pulled_state = None
pulled_zip_code = None


if st.checkbox("Check my location"):
    loc = get_geolocation()
    if loc:
        latitude = loc['coords']['latitude']
        longitude = loc['coords']['longitude']
        location = geolocator.reverse((latitude, longitude), exactly_one=True)

        if location:
            address_str = str(location)
            address_parts = address_str.split(',')
            pulled_city = address_parts[2].strip() if len(
                address_parts) > 2 else 'Unknown'
            pulled_state = address_parts[-3].strip() if len(
                address_parts) > 3 else 'Unknown'
            pulled_zip_code = address_parts[-2].strip() if len(
                address_parts) > 2 else 'Unknown'

        st.write(f"Your coordinates are {latitude}, {longitude}")
        st.write(f"Location: {pulled_city}, {pulled_state}, {pulled_zip_code}")
    else:
        st.write("Waiting for location...")

usZips = pd.read_csv("uszips.csv")

city_to_zipcodes = {}


def run_scrapy_spider(search_term, city, zip_code, state, max_pages):
    # Construct the command to run the spider with parameters
    file_name = generate_unique_filename(city, search_term)

    # Check if the JSON file exists
    json_file_path = f"cleaned{file_name}.json"
    csv_file_path = f"{generate_unique_filename(city, search_term)}.csv"
    csv_exists = file_exists(csv_file_path)
    json_exists = file_exists(json_file_path)
    st.write(f"JSON File Exists: {json_exists}")
    st.write(f"CSV File Exists: {csv_exists}")
    st.session_state['returned_json_file_path'] = json_file_path
    st.session_state['returned_csv_file_path'] = csv_file_path
    # Add the user_city_data elements to the dictionary with 'city' as the key

    # Extracting city, state, and zip code
    # The city is typically the third element from the start
    # The state is the second last element
    # The zip code is the third last element

    st.write(latitude, longitude)
    st.write(location)
    st.write(city, state, zip_code)

    command = [
        'scrapy', 'crawl', 'yelp-crawler',
        '-a', f'search={search_term}',
        '-a', f'city={city}',
        '-a', f'zip_code={zip_code}',
        '-a', f'state={state}',
        '-a', f'max_pages={max_pages}'
    ]
    # Run the command

    st.write(st.session_state['returned_json_file_path'])

    return json_file_path, csv_file_path


# Streamlit interface
st.title('Yelp Scrapy Spider')

# Create a button to toggle the sidebar's visibility

# Use a sidebar if the toggle button is not clicked
if not toggle_sidebar:
    selected_tab = st.sidebar.radio(
        "Choose a tab:", ["Input Form", "Show Table"])


# User input fields (inside the "Input Form" tab)
if toggle_sidebar or (selected_tab == "Input Form"):
    search_term = st.text_input('Search Term', 'fitness')
    city = st.text_input('City', pulled_city or '')
    zip_code = st.text_input('Zip Code', pulled_zip_code or '')
    state = st.text_input('State', pulled_state or '')

    # Maximum number value selector
    use_unlimited_pages = st.checkbox('Unlimited Pages', value=False)
    if not use_unlimited_pages:
        max_pages = st.number_input('Max Pages', min_value=1, step=1, value=2)

    # Button to start the spider
    if st.button('Run Spider'):
        if use_unlimited_pages:
            max_pages = False
        run_scrapy_spider(search_term, city, zip_code, state, max_pages)
     
        st.success('Spider run completed!')

# Displaying results (inside the "Show Results" tab)


def display_results_and_links(json_file_path, csv_file_path):

    if toggle_sidebar or (selected_tab == "Input Form"):
        json_file_path = st.session_state.get('returned_json_file_path')
        csv_file_path = st.session_state.get('returned_csv_file_path')

        if os.path.exists(json_file_path):
            with open(  json_file_path, 'r') as file:
                data = json.load(file)

            # Collapsible section for results
            with st.expander("View Results", expanded=False):
                # Display raw JSON data inside the expander
                st.json(data)

            # Provide a download link for the JSON file
            with open(  json_file_path, 'rb') as f:
                st.download_button(
                    label="Download JSON",
                    data=f,
                    file_name=  json_file_path,
                    mime='application/json'
                )
    # Displaying results (inside the "Show Results" tab)
    
    # Displaying results (inside the "Show Table" tab)
    if toggle_sidebar or (selected_tab == "Show Table"):

        st.write(json_file_path)
        st.write(json_file_path)
        if os.path.exists(json_file_path):
            with open(  json_file_path, 'r') as file:
                data = json.load(file)

            # Display JSON data as a table
            df = pd.DataFrame(data)
            st.write("JSON Table:")
            st.write(df)
        else:
            st.error('No data found. Please run the spider first.')

        if os.path.exists(csv_file_path):
            # Provide a download link for the CSV file
            with open(st.session_state['returned_csv_file_path'], 'rb') as f_csv:
                st.download_button(
                    label="Download CSV",
                    data=f_csv,
                    file_name=csv_file_path,
                    mime='text/csv',
                    key='download_csv_show_table'
                )
        else:
            st.warning(
                'No CSV data found. Please run the spider and generate CSV data.')


if st.button('Refresh'):
    st.experimental_rerun()


display_results_and_links(
    st.session_state['returned_json_file_path'], st.session_state['returned_csv_file_path'])
