import datetime
import os
from typing import List, Dict
import pandas as pd
import user_agent
from geopy.geocoders import Nominatim
import requests
import re

def get_user_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        location = data.get("city", "Unknown")
        return location
    except Exception as e:
        return "Unknown"
    

def clean_json_data(data_list: List[Dict]) -> List[Dict]:
    # Convert the list of dictionaries to a Pandas DataFrame
    df = pd.DataFrame(data_list)

    # Perform cleaning operations as before
    # ...

    # Convert the cleaned DataFrame back to a list of dictionaries
    cleaned_data_list = df.to_dict(orient='records')

    return cleaned_data_list


def file_exists(file_path):
    return os.path.exists(file_path)

def sanitize_for_filename(input_string):
    # Remove characters that are not safe for filenames
    sanitized_string = re.sub(r'[\\/:"*?<>|]+', '', input_string)
    return sanitized_string

def generate_unique_filename( user_location, search_terms):
    # Get the current date in the format: month-day-year
    search_terms = sanitize_for_filename(search_terms)
    user_location = sanitize_for_filename(user_location)
    current_date = datetime.datetime.now().strftime("%m-%d-%Y")

    # Remove spaces and special characters from search terms
    sanitized_search_terms = "".join(
        [c if c.isalnum() else "_" for c in search_terms])

    # Construct the file name using the provided information
    filename = f"{current_date}_{
        user_location}_{search_terms}"

    # Ensure the file name is unique in the current directory
    unique_filename = filename
    counter = 1
    while os.path.exists(unique_filename):
        unique_filename = f"{filename}_{counter}"
        counter += 1

    return unique_filename


# Example usage:
user_agent = "Mozilla/5.0"
user_location = "NewYork"
search_terms = {
    "search_term": "fitness",
    "city_search_term": "Denver",
    "city_zip_search_term": "80020",
    "state": "CO",
    "max_pages": 5
}

