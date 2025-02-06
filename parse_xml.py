import xml.etree.ElementTree as ET
from pathlib import Path
import argparse

def parse_xml(file_path, output_folder):
    tree = ET.parse(file_path)
    root = tree.getroot()
    ns = {'jats': 'https://jats.nlm.nih.gov/ns/archiving/1.3/'}

    content = []

    # Extract PMCID and construct PMC URL
    pmcid = root.find(".//jats:article-meta/jats:article-id[@pub-id-type='pmcid']", ns)
    pmc_url = ""
    if pmcid is not None and pmcid.text:
        pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid.text}/"
        print(f"PMC URL: {pmc_url}")
    else:
        print("PMCID not found")
    content.append(f"Link: {pmc_url}\n")

    # Extract title
    title = root.find(".//jats:article-title", ns)
    title_text = title.text if title is not None else "No title available"
    content.append(f"Title: {title_text}\n")

    # Extract abstract
    abstract = root.find(".//jats:abstract", ns)
    abstract_text = ""
    if abstract is not None:
        abstract_text = " ".join([elem.text for elem in abstract.findall(".//jats:p", ns) if elem.text])
    content.append(f"Abstract: {abstract_text}\n")

    # Extract body
    body = root.find(".//jats:body", ns)
    if body is not None:
        content.append("Body:")
        for section in body.findall(".//jats:sec", ns):
            section_title = section.find("jats:title", ns)
            if section_title is not None and section_title.text:
                content.append(f"\n{section_title.text}\n" + "-" * len(section_title.text))
            paragraphs = section.findall(".//jats:p", ns)
            for para in paragraphs:
                if para.text:
                    content.append(para.text)
    else:
        content.append("No body text found")

    # Save the parsed content to a text file
    output_file = output_folder / f"{file_path.stem}.txt"
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("\n".join(content))

    print(f"Saved to {output_file}")

def process_folder(trials_folder, output_folder):
    trials_folder = Path(trials_folder)
    output_folder = Path(output_folder)

    output_folder.mkdir(parents=True, exist_ok=True)

    for file in trials_folder.glob("*.xml"):
        parse_xml(file, output_folder)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse XML files and save their content as .txt files.")
    parser.add_argument("trials-folder", help="Path to the folder containing trial XML files.")
    parser.add_argument("output-folder", help="Path to the folder where parsed .txt files will be saved.")

    args = parser.parse_args()
    process_folder(args.trials_folder, args.output_folder)
