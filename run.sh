#!/bin/bash

API_KEY_PATH=""
TEMPORARY_XML_FOLDER="trials_xml"
TRIALS_FOLDER="trials"
SCRAPE_SCRIPT="scrape.py"
PARSE_SCRIPT="parse_xml.py"
CLASSIFY_SCRIPT="summarize.py"

# Ensure folders exist
if [ ! -d "$TEMPORARY_XML_FOLDER" ]; then
    echo "Creating xml file folder at $TEMPORARY_XML_FOLDER..."
    mkdir -p "$TEMPORARY_XML_FOLDER"
fi

if [ ! -d "$TRIALS_FOLDER" ]; then
    echo "Creating trials folder at $TRIALS_FOLDER..."
    mkdir -p "$TRIALS_FOLDER"
fi

# Step 1: scraping into xml files
echo "Running the article scraping script..."
python3 "$SCRAPE_SCRIPT" "clinical trial fitbit" "$TEMPORARY_XML_FOLDER" --max_articles 2
if [ $? -ne 0 ]; then
    echo "Error running the scraping script. Exiting."
    exit 1
fi
echo "Article scraping completed."

# Step 2: format collected xml files into a readable format in txt
echo "Running the xml parsing script..."
python3 "$PARSE_SCRIPT" "$TEMPORARY_XML_FOLDER" $TRIALS_FOLDER

# Step 3: classify/summarize
echo "Running the article classification script..."
python3 "$CLASSIFY_SCRIPT" --api-key-path "$API_KEY_PATH" --trials-folder "$TRIALS_FOLDER"
if [ $? -ne 0 ]; then
    echo "Error running the classification script. Exiting."
    exit 1
fi
echo "Article classification and summarization completed."

echo "All tasks completed successfully."
