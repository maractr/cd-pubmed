import json
import os
from Bio import Entrez
import requests
from bs4 import BeautifulSoup

MAX_RESULTS = 50
QUERY = "fitbit" # Replace with device of choice
processed_pmids = set()
os.makedirs('trials_old', exist_ok=True)

Entrez.email = None # Replace with email
BIOC_URL = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pubmed.cgi/BioC_json"


# search pubmed for ids
def search_pubmed(query, max_results=10):
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()
    return record['IdList']

# get metadata from pubmed
def fetch_full_text_links(id_list):
    ids = ','.join(id_list)
    handle = Entrez.efetch(db="pubmed", id=ids, retmode="xml")
    records = Entrez.read(handle)
    handle.close()

    articles_info = []
    for article in records['PubmedArticle']:
        title = article['MedlineCitation']['Article']['ArticleTitle']
        pmid = article['MedlineCitation']['PMID']
        doi = None
        journal = article['MedlineCitation']['Article']['Journal']
        journal_name = journal['Title']
        issn = journal.get('ISSN', 'N/A')
        for link in article['PubmedData']['ArticleIdList']:
            if link.attributes.get('IdType') == 'doi':
                doi = link

        # check duplicates
        if pmid in processed_pmids:
            print(f"Duplicate: PMID: {pmid}, Title: {title}")
            continue

        full_text = get_unpaywall_link(doi)
        if full_text is None:
            full_text = 'N/A'
        else:
            save_full_text_as_file(pmid, full_text)  # Save

        processed_pmids.add(pmid)

        articles_info.append({'pmid': pmid, 'title': title, 'doi': doi, 'journal': journal_name,
                              'issn': issn, 'fullText': full_text})

    return articles_info


# Query Unpaywall
def get_unpaywall_link(doi):
    if doi is None:
        return None
    base_url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": Entrez.email}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get('is_oa'):
            return data.get('best_oa_location', {}).get('url')
    return None


def save_full_text_as_file(pmid, full_text_url):
    try:
        response = requests.get(full_text_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, features="html.parser")
            article_text = '\n'.join([p.get_text() for p in soup.find_all('p')])

            if article_text.strip():  # only save if there's content
                file_path = f"trials_old/{pmid}.txt"
                with open(file_path, "w", encoding='utf-8') as text_file:
                    text_file.write(article_text)
                print(f"Full text saved for {pmid}")
            else:
                print(f"No article text found for  {pmid}")
        else:
            print(f"Failed to retrieve full text for {pmid}")
    except Exception as e:
        print(f"Error saving full text for {pmid}: {str(e)}")


# Main query
pubmed_ids = search_pubmed(QUERY, max_results=MAX_RESULTS)
articles_with_full_text = fetch_full_text_links(pubmed_ids)

# Save articles to JSON file
with open("articles.json", "w") as outfile:
    json.dump(articles_with_full_text, outfile, indent=4)

print(f"Articles saved")

# Optional: print stats regarding collected texts
# for pmid, title, doi, journal_name, issn, pubmed_id in articles_with_full_text:
#     print(f"PMID: {pmid}")
#     print(f"Title: {title}")
#     print(f"Journal Name: {journal_name}")
#     print(f"ISSN: {issn}")
#     print(f"PubMed ID: {pubmed_id}")
#
#     found_full_text = False
#
#     if doi:
#         # Try to get full text from Unpaywall
#         unpaywall_url = get_unpaywall_link(doi, EMAIL)
#         if unpaywall_url:
#             print(f"Full Text (Unpaywall): {unpaywall_url}\n")
#             found_full_text = True
#         else:
#             print(f"DOI: {doi} (No open access found on Unpaywall)\n")
#
#     # Update full text count
#     if found_full_text:
#         full_text_count += 1
#
#     if journal_name in journal_counts:
#         journal_counts[journal_name] += 1
#     else:
#         journal_counts[journal_name] = 1
#
#     journal_info = get_journal_metadata(issn)
#     if journal_info:
#         print(f"Journal Title: {journal_info['title']}")
#         print(f"Impact Factor: {journal_info['impact_factor']}")
#         print(f"Description: {journal_info['description']}")
#
# full_text_percentage = (full_text_count / total_articles) * 100 if total_articles > 0 else 0
# print("\n--- Summary Statistics ---")
# print(f"Total Articles: {total_articles}")
# print(f"Full Text Found: {full_text_count} ({full_text_percentage:.2f}%)\n")
#
# print("--- Journal Counts ---")
# for journal, count in journal_counts.items():
#     print(f"{journal}: {count}")
