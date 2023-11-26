# streamlit_app.py
import streamlit as st
import subprocess
import json
import pandas as pd
import os

# Function to trigger Scrapy spider


def run_scrapy_spider(search_term, city, zip_code, state):
    # Construct the command to run the spider with parameters
    command = [
        'scrapy', 'crawl', 'yelp-crawler',
        '-a', f'search={search_term}',
        '-a', f'city={city}',
        '-a', f'zip_code={zip_code}',
        '-a', f'state={state}'
    ]
    # Run the command
    subprocess.run(command)


# Streamlit interface
st.title('Yelp Scrapy Spider')

# User input fields
search_term = st.text_input('Search Term', 'fitness')
city = st.text_input('City', 'Denver')
zip_code = st.text_input('Zip Code', '80020')
state = st.text_input('State', 'CO')

# Button to start the spider
if st.button('Run Spider'):
    run_scrapy_spider(search_term, city, zip_code, state)
    st.success('Spider run completed!')

# Displaying results
if st.button('Show Results'):
    if os.path.exists('cleaned_extracted_data.json'):
        with open('cleaned_extracted_data.json', 'r') as file:
            data = json.load(file)

            # Collapsible section for results
            with st.expander("View Results", expanded=False):
                # Display raw JSON data inside the expander
                st.json(data)

            # Provide a download link for the JSON file
            with open('cleaned_extracted_data.json', 'rb') as f:
                st.download_button(
                    label="Download JSON",
                    data=f,
                    file_name='cleaned_extracted_data.json',
                    mime='application/json'
                )
    else:
        st.error('No data found. Please run the spider first.')
