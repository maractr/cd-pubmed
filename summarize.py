import argparse
import os
from openai import OpenAI
import time

parser = argparse.ArgumentParser(description="Classify and summarize clinical trials.")
parser.add_argument("--api-key-path", type=str, required=True, help="Path to the OpenAI API key file.")
parser.add_argument("--trials-folder", type=str, required=True, help="Folder containing the clinical trial files.")
args = parser.parse_args()

API_KEY_PATH = args.api_key_path
TRIALS_FOLDER = args.trials_folder
OUTPUT_FOLDER = r"./summaries"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

key = ''

with open(API_KEY_PATH, 'r') as file:
    key = file.read().strip()

client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

PROMPT_DEVICE_NAME = 'FitBit'
OUTPUT_LENGTH = 300  # word count for the thesis
MEDICAL_FIELDS = ["Somnology", "Gynecology", "Obstetrics", "Cardiology", "General Physiology",
                  "Endocrinology", "Bariatrics", "Psychiatry", "Oncology", "Gastroenterology", "Pulmonology",
                  "Chronic pain or diseases", "Nephrology", "Other"]

def read_clinical_trial_files(folder_path):
    """
    Reads all text files from the specified folder and returns their content along with titles.
    """
    trials = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                # Extract the title if it exists
                title = ""
                if "Title:" in content:
                    title_start = content.index("Title:") + len("Title:")
                    title_end = content.find("\n", title_start)
                    title = content[title_start:title_end].strip()
                # Extract url 
                url = ""
                if "Link:" in content:
                    url_start = content.index("Link:") + len("Link:")
                    url_end = content.find("\n", url_start)
                    url = content[url_start:url_end].strip()
                trials.append({"title": title, "content": content, "url": url})
    return trials

def classify_medical_field(trial_text):
    """
    Uses OpenAI's GPT model to classify the clinical trial into a medical field.
    """
    prompt = (
        f'''You are provided with a set of 14 medical field classes: \"Somnology\", \"Gynecology\", \"Obstetrics\", \"Cardiology\", \"General Physiology\", \"Endocrinology\", \"Bariatrics\", \"Psychiatry\", \"Oncology\", \"Gastroenterology\", \"Pulmonology\", \"Chronic pain or diseases\", \"Neprhology\", and \"Other\". 
Your task is to analyze the given clinical trial description and classify it into one of these 14 medical field classes. Please provide only one field as your output.
---
Trial Description: {trial_text[0:400]}
---
Task: Classify the clinical trial into one of the 14 specified medical field classes:
- Somnology
- Gynecology
- Obstetrics
- Cardiology
- General Physiology
- Endocrinology
- Bariatrics
- Psychiatry
- Oncology
- Gastroenterology
- Pulmonology
- Chronic pain or diseases
- Nephrology
- Other
Please provide only the medical field name as your output.
'''
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that classifies clinical trials into medical fields."},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.3,
            max_tokens=50
        )
        msg = response.choices[0].message.content.strip()
        for field in MEDICAL_FIELDS:
            if field in msg:
                classified_field = field
                break
        else:
            classified_field = 'Other'
        return classified_field
    except Exception as e:
        print(trial_text)
        print(f"Error during classification: {e}")
        return "Unknown"


def extract_summary(trial_text):
    """
    Extracts the summary (e.g., Abstract) from the clinical trial text.
    """
    try:
        abstract_start = trial_text.index("Abstract:") + len("Abstract:")
        body_start = trial_text.index("Body:", abstract_start)
        abstract = trial_text[abstract_start:body_start].strip()
        return abstract
    except ValueError:
        # If "Abstract:" or "Body:" not found, return a portion of the text
        return trial_text[:500]

def generate_thesis(summaries, urls, device_name, medical_field, output_length):
    """
    Constructs the prompt and generates a concise thesis using GPT.
    Includes a references section with citation numbers matched to urls.
    """
    summary_index = len(summaries)
    summaries_combined = "\n\n".join([f"{i + 1}. {summary}" for i, summary in enumerate(summaries)])
    references_section = "\n".join([f"[{i + 1}] {url}" for i, url in enumerate(urls)])

    prompt = f'''Your task is to extract relevant information from the {summary_index} inputted summaries labeled from 1 to {summary_index} to construct an argument about the purpose of {device_name} in {medical_field} trials. 
Each summary includes in-line references to clinical trials in the following format: [1]. Your reader will be clinical research coordinators.
---
Summary:
{summaries_combined}
---
Task: Write a concise {output_length}-word thesis about the purpose of {device_name} in {medical_field} trials. Use the numeric in-line citation format [1], [2], etc., to reference sources. Do not fabricate references or cite summaries that do not support the claim. Ensure every source is cited at least once, and citations are strictly sequential. At the end, include a "References" section with each citation number and its corresponding URL, and do not format the word "References" with any markdown:
---
References:
{references_section}
'''

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system",
                 "content": "You are a knowledgeable assistant skilled in constructing scientific arguments based on provided summaries."},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.5,
            max_tokens=output_length * 5
        )
        thesis = response.choices[0].message.content.strip()
        return thesis
    except Exception as e:
        print(f"Error during thesis generation: {e}")
        return ""

def filter_trials_by_device(trial_texts, device_name):
    """
    Filters out trials that do not contain the device_name in their text.
    """
    filtered_trials = []
    for trial in trial_texts:
        title = trial["title"]
        content = trial["content"]
        url = trial["url"]

        if device_name.lower() in title.lower() or "wearable" in title.lower():
            filtered_trials.append({"title": title, "content": content, "url": url})
    return filtered_trials

def main():
    # Read files
    print("Reading clinical trial files...")
    trial_texts = read_clinical_trial_files(TRIALS_FOLDER)
    print(f"Total trials found: {len(trial_texts)}")

    device_name = "FitBit"

    # Keep trials that contain the device name
    filtered_trials = filter_trials_by_device(trial_texts, device_name)
    print(f"Trials containing the device name '{device_name}': {len(filtered_trials)}")
    classified_trials = {}

    for idx, trial in enumerate(filtered_trials, 1):
        print(f"Processing Trial {idx}/{len(filtered_trials)}...")

        abstract = extract_summary(trial["content"])
        medical_field = classify_medical_field(abstract)

        if medical_field not in classified_trials:
            classified_trials[medical_field] = {"summaries": [], "urls": []}
        classified_trials[medical_field]["summaries"].append(abstract)
        classified_trials[medical_field]["urls"].append(trial["url"])

        time.sleep(1)

    print("\nClassification complete!")
    for field, data in classified_trials.items():
        summaries = data["summaries"]
        urls = data["urls"]
        print(f"\nGenerating thesis for Medical Field: {field}")
        thesis = generate_thesis(summaries, urls, device_name, field, OUTPUT_LENGTH)
        print(f"Thesis for {field}:\n{thesis}\n")

        thesis_filename = os.path.join(OUTPUT_FOLDER, f"thesis_{field.replace(' ', '_').lower()}.txt")
        with open(thesis_filename, 'w', encoding='utf-8') as f:
            f.write(thesis)
        print(f"Thesis saved to {thesis_filename}")


if __name__ == "__main__":
    main()
