import pandas as pd
from transformers import pipeline
import json
import os # Import os for checking file existence

# --- Configuration ---
sample_file_path = 'ShortenDataset_News.csv'

# Define your 8 target categories exactly as desired for zero-shot classification
target_categories = [
    "Entertainment", "Education", "Politics", "Technology",
    "Socio-Cultural", "Economy", "Sports", "Crime"
]

# --- Script Start ---
print("--- Starting data processing script ---")

# 0. Check if the sample file exists
if not os.path.exists(sample_file_path):
    print(f"Error: The sample file '{sample_file_path}' was not found in the current directory.")
    print("Please ensure your sample CSV file is in the same folder as this Python script.")
    exit() # Exit the script if the file is not found

# 1. Read CSV File
try:
    df = pd.read_csv(sample_file_path)
    print("\n--- Head of your DataFrame (after initial load) ---")
    print(df.head())
    print("\n--- Data types after initial load ---")
    print(df.dtypes)
except Exception as e:
    print(f"Error reading CSV file: {e}")
    print("Please ensure the CSV file is not open in another program and its name is correct.")
    exit()


# 2. Convert 'publish_date' to Date Format
# Ensure 'publish_date' column exists and is handled.
if 'publish_date' in df.columns:
    df['publish_date'] = pd.to_datetime(df['publish_date'], format='%Y%m%d', errors='coerce')
    # Drop rows where the publish_date couldn't be correctly parsed (they'll have 'NaT')
    df.dropna(subset=['publish_date'], inplace=True)
    print("\n--- DataFrame Head after date conversion and dropping invalid rows ---")
    print(df.head())
    print("\n--- Data types after date conversion ---")
    print(df.dtypes)
else:
    print("\nError: 'publish_date' column not found in your CSV. Please check your CSV headers.")
    exit()


# 3. Add 'News Sentiment' Column using GenAI
# This part downloads the sentiment model on the first run.
sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

def get_sentiment_score(text):
    if pd.isna(text) or str(text).strip() == "":
        return 0.0 # Assign a neutral score for empty/missing text
    try:
        result = sentiment_analyzer(text)
        label = result[0]['label']
        score = result[0]['score']
        # Map labels to a -1 to 1 range (common output for this type of model)
        if label == 'LABEL_2' or label.lower() == 'positive': return score
        elif label == 'LABEL_0' or label.lower() == 'negative': return -score
        else: return 0.0 # Neutral (LABEL_1 or other interpretations)
    except Exception as e:
        # Log errors for debugging without crashing for every bad entry
        print(f"Error processing sentiment for text '{str(text)[:50]}...': {e}")
        return 0.0

print("\n--- Running sentiment analysis... This might take some time for your sample size ---")
# Ensure 'headline_text' column exists before applying sentiment analysis
if 'headline_text' in df.columns:
    df['news_sentiment'] = df['headline_text'].apply(get_sentiment_score)
else:
    print("\nError: 'headline_text' column not found for sentiment analysis. Please check your CSV headers.")
    exit()


# 4. Automatically Classify 'headline_category' using Zero-Shot GenAI
# This GenAI model classifies text into categories it hasn't seen during training,
# based on its general language understanding.
# This will download the zero-shot model on the first run.
# Ensure 'headline_text' column is available for classification.
if 'headline_text' in df.columns:
    category_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    def classify_headline_category(text):
        if pd.isna(text) or str(text).strip() == "":
            return "Socio-Cultural" # Default to a broad category if text is empty/missing
        try:
            # multi_label=False ensures it picks only the single best category
            result = category_classifier(text, candidate_labels=target_categories, multi_label=False)
            return result['labels'][0] # The highest-scoring label
        except Exception as e:
            print(f"Error classifying category for text '{str(text)[:50]}...': {e}")
            return "Socio-Cultural" # Default to Socio-Cultural on error

    print("\n--- Running AI-driven category classification... This might take some time ---")
    df['category'] = df['headline_text'].apply(classify_headline_category)

    # Filter to only include your 8 desired categories. Rows not mapped by AI to these will be dropped.
    df = df[df['category'].isin(target_categories)]

    print("\n--- DataFrame Head after Category processing and sentiment ---")
    print(df[['publish_date', 'category', 'news_sentiment', 'headline_text']].head())
    print("\n--- Value Counts for AI-assigned Categories ---")
    print(df['category'].value_counts())
else:
    print("\nError: 'headline_text' column not found for category classification. Please check your CSV headers.")
    exit()


# 5. Prepare Data for Individual Headline Output per Year (JSON Structure)
df['Year'] = df['publish_date'].dt.year.astype(str)

# Sort by publish_date to ensure chronological order within years for visualization
df = df.sort_values('publish_date')

processed_data_by_year = {}

# Iterate through each year and gather its headlines
for year, year_group in df.groupby('Year'):
    # Select only the relevant columns and convert to a list of dictionaries
    headlines_for_year = year_group[['publish_date', 'category', 'news_sentiment', 'headline_text']].to_dict(orient='records')

    # Convert datetime objects to string for JSON serialization
    for item in headlines_for_year:
        # Item['publish_date'] is already a datetime object due to earlier step, format it.
        item['publish_date'] = item['publish_date'].strftime('%Y-%m-%d') # Format as YYYY-MM-DD string

    processed_data_by_year[year] = headlines_for_year

# 6. Save to JSON
output_file_name = 'news_spline_data_individual_headlines.json'
try:
    with open(output_file_name, 'w', encoding='utf-8') as f:
        json.dump(processed_data_by_year, f, indent=4, ensure_ascii=False)
    print(f"\n--- Data processing complete for individual headlines per year ---")
    print(f"Aggregated data saved to {output_file_name}")
    print(f"Total years processed: {len(processed_data_by_year)}")
    # Example: print number of headlines for a specific year (e.g., 2001)
    if '2001' in processed_data_by_year:
        print(f"Headlines in 2001: {len(processed_data_by_year['2001'])}")
except Exception as e:
    print(f"Error saving JSON file: {e}")
    print("Please check write permissions for the project folder.")

print("\n--- Script finished ---")