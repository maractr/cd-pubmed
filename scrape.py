import requests
import os
import argparse

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PMC_BASE_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/"
PMC_OAI_URL = "https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi"

def search_pubmed(term, max_articles=5):
    """Search PubMed and return a list of PMIDs."""
    url = f"{BASE_URL}esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": max_articles
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data["esearchresult"]["idlist"]

def find_pmc_id(pmid):
    """Find PMC ID for a given PubMed PMID."""
    url = f"{BASE_URL}elink.fcgi"
    params = {
        "dbfrom": "pubmed",
        "linkname": "pubmed_pmc",
        "id": pmid,
        "retmode": "json"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    try:
        pmc_id = data["linksets"][0]["linksetdbs"][0]["links"][0]
        return pmc_id
    except (IndexError, KeyError):
        return None

def download_pmc_full_text(pmc_id, folder):
    """Download full text of article from PMC"""
    params = {
        "verb": "GetRecord",
        "identifier": f"oai:pubmedcentral.nih.gov:{pmc_id}",
        "metadataPrefix": "pmc"
    }
    response = requests.get(PMC_OAI_URL, params=params)
    response.raise_for_status()

    full_text_xml = response.text
    file_name = f"pmc_{pmc_id}.xml"
    file_path = os.path.join(folder, file_name)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(full_text_xml)
    print(f"Full text saved as {file_path}")
    return file_path

def fetch_multiple_articles(term, folder, max_articles=5):
    pmids = search_pubmed(term, max_articles)
    print(f"Found {len(pmids)} articles with PMIDs: {pmids}")

    for pmid in pmids:
        print(f"\nProcessing article with PMID: {pmid}")
        pmc_id = find_pmc_id(pmid)

        if pmc_id:
            print(f"PMC ID found: {pmc_id}, downloading")
            file_path = download_pmc_full_text(pmc_id, folder)
            print(f"Full text {pmid} saved as {file_path}")
        else:
            print(f"No PMC full text available for {pmid}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch articles from PubMed and save their full texts.")
    parser.add_argument("term", help="Search term for PubMed articles.")
    parser.add_argument("folder", help="Folder to save the downloaded articles.")
    parser.add_argument("--max_articles", type=int, default=5, help="Maximum number of articles to fetch (default: 5).")
    
    args = parser.parse_args()

    # Ensure the folder exists
    os.makedirs(args.folder, exist_ok=True)
    
    fetch_multiple_articles(args.term, args.folder, args.max_articles)
