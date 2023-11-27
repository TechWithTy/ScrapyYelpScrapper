import streamlit as st
import json
import os
import pandas as pd
from utils import generate_unique_filename

# Function to check if a file exists


def file_exists(file_path):
    return os.path.exists(file_path)

# Function to generate a unique filename



# Streamlit interface
st.title('Check File Existence and Show Results')

# User input fields
city = st.text_input('City', 'Aurora')
search_term = st.text_input('Search Term', 'fitness')

file_name = generate_unique_filename(city, search_term)

json_file_path = f"cleaned{file_name}.json"
csv_file_path = f"{generate_unique_filename(city, search_term)}.csv"
csv_exists = file_exists(csv_file_path)
json_exists = file_exists(json_file_path)
st.write(f"JSON File Exists: {json_exists}")
st.write(f"CSV File Exists: {csv_exists}")

st.write(json_file_path)
st.write(csv_file_path)

# Display file existence status


# Displaying results
if json_exists:
    with open('11-26-2023_Aurora_fitness.json', 'r') as json_file:
        data = json.load(json_file)
        st.write("JSON Data:")
        st.json(data)

if csv_exists:
    df = pd.read_csv("11-26-2023_Aurora_fitness.csv")
    st.write("CSV Data:")
    st.write(df)
