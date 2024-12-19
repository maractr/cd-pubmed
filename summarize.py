import argparse
import os
import openai
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

with open(API_KEY_PATH, 'r') as file:
    openai.api_key = file.read().strip()

with open(API_KEY_PATH, 'r') as file:
    content = file.read()
    openai.api_key = content
PROMPT_DEVICE_NAME = 'FitBit'
OUTPUT_LENGTH = 300  # word count for the thesis
MEDICAL_FIELDS = ["Somnology", "Gynecology", "Obstetrics", "Cardiology", "General Physiology",
                  "Endocrinology", "Bariatrics", "Psychiatry", "Oncology", "Gastroenterology", "Pulmonology",
                  "Chronic pain or diseases", "Nephrology", "Other"]

def read_clinical_trial_files(folder_path):
    """
    Reads all text files from the specified folder and returns their content.
    """
    trial_texts = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                trial_texts.append(content)
    return trial_texts


def classify_medical_field(trial_text):
    """
    Uses OpenAI's GPT model to classify the clinical trial into a medical field.
    """
    prompt = (
        f'''You are provided with a set of 14 medical field classes: \"Somnology\", \"Gynecology\", \"Obstetrics\", \"Cardiology\", \"General Physiology\", \"Endocrinology\", \"Bariatrics\", \"Psychiatry\", \"Oncology\", \"Gastroenterology\", \"Pulmonology\", \"Chronic pain or diseases\", \"Neprhology\", and \"Other\". 
Your task is to analyze the given clinical trial description and classify it into one of these 14 medical field classes. Please provide only one field as your output.
---
Trial Description: {trial_text[0:500]}
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
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that classifies clinical trials into medical fields."},
                {"role": "user", "content": prompt}
            ],
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


def generate_thesis(summaries, device_name, medical_field, output_length):
    """
    Constructs the prompt and generates a concise thesis using GPT.
    """
    summary_index = len(summaries)
    summaries_combined = "\n\n".join([f"{i + 1}. {summary}" for i, summary in enumerate(summaries)])

    prompt = f'''Your task is to extract relevant information from the {summary_index} inputted summaries labeled from 1 to {summary_index} to construct an argument about the purpose of {device_name} in {medical_field} trials. 
            Each summary includes in-line references to clinical trials in the following format: [1]. Your reader will be clinical research coordinators.
            ---
            Summary:
            {summaries_combined}
            ---
            Task: Write a concise {output_length}-word thesis about the purpose of {device_name} in {medical_field} trials. Use the numeric in-line citation format [1], [2], etc., to reference sources as appropriate.'''

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "You are a knowledgeable assistant skilled in constructing scientific arguments based on provided summaries."},
                {"role": "user", "content": prompt}
            ],
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

    Parameters:
    - trial_texts (list): List of trial texts.
    - device_name (str): The name of the device to look for in the text.

    Returns:
    - filtered_trials (list): List of trial texts that contain the device_name.
    """
    filtered_trials = []

    for trial in trial_texts:
        if device_name.lower() in trial.lower():
            filtered_trials.append(trial)

    return filtered_trials

def main():
    # Read files
    print("Reading clinical trial files...")
    trial_texts = read_clinical_trial_files(TRIALS_FOLDER)
    print(f"Total trials found: {len(trial_texts)}")

    device_name = "FitBit"

    # Keep trials that contain the device name, tossing out trials that shouldn't be there
    filtered_trials = filter_trials_by_device(trial_texts, device_name)
    print(f"Trials containing the device name '{device_name}': {len(filtered_trials)}")
    classified_trials = {}

    for idx, trial in enumerate(filtered_trials, 1):
        print(f"Processing Trial {idx}/{len(filtered_trials)}...")

        abstract = extract_summary(trial)
        medical_field = classify_medical_field(abstract)

        if medical_field not in classified_trials:
            classified_trials[medical_field] = []
        classified_trials[medical_field].append(abstract)

        time.sleep(1)

    print("\nClassification complete!")
    for field, summaries in classified_trials.items():
        print(f"\nGenerating thesis for Medical Field: {field}")
        thesis = generate_thesis(summaries, device_name, field, OUTPUT_LENGTH)
        print(f"Thesis for {field}:\n{thesis}\n")

        thesis_filename = os.path.join(OUTPUT_FOLDER, f"thesis_{field.replace(' ', '_').lower()}.txt")
        with open(thesis_filename, 'w', encoding='utf-8') as f:
            f.write(thesis)
        print(f"Thesis saved to {thesis_filename}")


if __name__ == "__main__":
    main()
