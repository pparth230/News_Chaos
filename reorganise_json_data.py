import json
from datetime import datetime
import os

# --- Configuration ---
# Path to existing JSON file (output from previous Step 10)
input_json_file = 'news_spline_data_individual_headlines.json'
# Name for the new JSON file with monthly grouping
output_json_file = 'news_spline_data_monthly_headlines.json'

print(f"--- Starting JSON reorganization script ---")

# 1. Load the existing JSON data
if not os.path.exists(input_json_file):
    print(f"Error: Input JSON file '{input_json_file}' not found.")
    print("Please ensure your JSON file is in the same folder as this script.")
    exit()

try:
    with open(input_json_file, 'r', encoding='utf-8') as f:
        all_news_by_year = json.load(f)
    print(f"Successfully loaded data from '{input_json_file}'.")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON from '{input_json_file}': {e}")
    print("Please ensure the JSON file is valid.")
    exit()
except Exception as e:
    print(f"An unexpected error occurred while loading JSON: {e}")
    exit()


# 2. Reorganize data by Year and then by Month
processed_data_by_year_month = {}

for year, headlines_list in all_news_by_year.items():
    processed_data_by_year_month[year] = {} # Initialize dictionary for months within this year

    print(f"Processing year: {year} with {len(headlines_list)} headlines...")

    for headline in headlines_list:
        # Parse the publish_date string back to a datetime object
        # It's already in 'YYYY-MM-DD' format, so we use strptime
        try:
            publish_date_obj = datetime.strptime(headline['publish_date'], '%Y-%m-%d')
            month = str(publish_date_obj.month) # Get month as string
        except ValueError as e:
            print(f"Warning: Could not parse date '{headline['publish_date']}' for headline: {headline['headline_text'][:50]}... Error: {e}")
            continue # Skip this headline or handle appropriately

        if month not in processed_data_by_year_month[year]:
            processed_data_by_year_month[year][month] = [] # Initialize list for headlines in this month

        # Add the entire headline dictionary to the respective month's list
        processed_data_by_year_month[year][month].append(headline)

print("\n--- Data reorganization complete ---")

# 3. Save the new, reorganized JSON data
try:
    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data_by_year_month, f, indent=4, ensure_ascii=False)
    print(f"Reorganized data saved to '{output_json_file}'.")
except Exception as e:
    print(f"Error saving reorganized JSON file: {e}")
    print("Please check write permissions for the project folder.")

print("\n--- Script finished ---")