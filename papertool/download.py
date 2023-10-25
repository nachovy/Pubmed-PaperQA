import argparse
import subprocess
import os
import urllib.request
import NCBIQuery
import json
from tqdm import tqdm
from bs4 import BeautifulSoup
from .scihub.scihub import SciHub
from .sciencedirect import get_sciencedirect

def get_arguments():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--id", type=str, help="A single pmid of a paper.")
    group.add_argument(
        "--id_file",
        type=str,
        default="./paper_ids.txt",
        help="Path to the file containing pmids of the papers to be downloaded. "
        "Default path './paper_ids.txt'.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./saved_papers",
        help="Folder to store downloaded papers. Default path './saved_papers'.",
    )
    parser.add_argument(
        "--abstract", action="store_true", help="Download abstracts only."
    )
    return parser.parse_args()


def pmid_to_doi(pmid):
    pmid = str(pmid)
    base_url = "https://pubmed.ncbi.nlm.nih.gov/"
    url = base_url + pmid
    try:
        content = urllib.request.urlopen(url).read()
    except Exception as exception:
        print(exception)
        return None
    soup = BeautifulSoup(content, "lxml")
    doispans = soup.find_all("span", class_="citation-doi")
    if len(doispans) == 0:
        return None
    return doispans[0].contents[0].strip()[5:-1]


def pmid_to_pmcid(pmid):
    pmid = str(pmid)
    base_url = "https://pubmed.ncbi.nlm.nih.gov/"
    url = base_url + pmid
    try:
        content = urllib.request.urlopen(url).read()
    except Exception as exception:
        print(exception)
        return
    soup = BeautifulSoup(content, "lxml")
    pmcida = soup.find_all("a", {"data-ga-action": "PMCID"})
    if len(pmcida) == 0:
        return None
    return pmcida[0].contents[0].strip()


def get_pmc(id_list, output_dir):
    base_url = "https://www.ncbi.nlm.nih.gov/pmc/articles/"
    print("Trying to get papers with free access in PMC...")
    for id_ in tqdm(id_list):
        pdf_path = os.path.join(output_dir, id_ + ".pdf")
        html_path = os.path.join(output_dir, id_ + ".html")
        if os.path.exists(pdf_path) or os.path.exists(html_path):
            continue
        pmcid = pmid_to_pmcid(id_)
        if pmcid is not None:
            pdf_url = base_url + pmcid + "/pdf/"
            try:
                opener = urllib.request.build_opener()
                opener.addheaders = [
                    (
                        "User-agent",
                        "Mozilla/5.0 (Windows NT 5.2; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
                    )
                ]
                urllib.request.install_opener(opener)
                urllib.request.urlretrieve(pdf_url, pdf_path)
            except urllib.error.HTTPError as error:
                try:
                    html_url = base_url + pmcid + "/?report=printable"
                    raw_html = urllib.request.urlopen(html_url).read()
                    with open(html_path, 'wb') as f:
                        f.write(raw_html)
                except:
                    pass
            except Exception as exception:
                print(exception)
                continue


def get_scihub(id_list, output_dir):
    scihub = SciHub()
    print("Trying to get papers using scihub.py...")
    for id_ in tqdm(id_list):
        pdf_path = os.path.join(output_dir, id_ + ".pdf")
        html_path = os.path.join(output_dir, id_ + ".html")
        if os.path.exists(pdf_path) or os.path.exists(html_path):
            continue
        doi = pmid_to_doi(id_)
        if doi is not None:
            try:
                scihub.download(doi, destination=output_dir, path=id_ + ".pdf")
            except Exception:
                return

def get_elsevier_api(pmid_list, output_dir):
    from elsapy.elsclient import ElsClient
    from elsapy.elsprofile import ElsAuthor, ElsAffil
    from elsapy.elsdoc import FullDoc, AbsDoc
    from elsapy.elssearch import ElsSearch
    
    ## Initialize client
    client = ElsClient(api_key="dbfef42409dbf570deb66c8fd06e9fb9")
    for pmid in tqdm(pmid_list):
        filename = os.path.join(output_dir, f"{pmid}.txt")
        filename_pdf = os.path.join(output_dir, f"{pmid}.pdf")
        filename_html = os.path.join(output_dir, f"{pmid}.html")
        if os.path.exists(filename) or os.path.exists(filename_pdf) or os.path.exists(filename_html):
            continue
        doi = pmid_to_doi(pmid)
        if doi is not None:
            doi_doc = FullDoc(doi = doi)
            if doi_doc.read(client):
                doi_doc.write()
                text = doi_doc.data['coredata']['dc:description']
                if text is None:
                    continue
                texts = " ".join(text.split('\n'))
                if type(doi_doc.data['originalText']) is str:
                    with open(filename, 'w') as f: 
                        f.write(doi_doc.data['originalText'])


if __name__ == "__main__":
    args = get_arguments()
    if args.abstract:
        if args.id is not None:
            id_list = [args.id]
        else:
            with open(args.id_file, "r", encoding='utf-8') as f:
                id_list = f.read().splitlines()
        print("Trying to get abstracts...")
        new_id_list = []
        for id_ in id_list:
            output_file = os.path.join(args.output_dir, id_ + ".txt")
            if not os.path.exists(output_file):
                new_id_list.append(id_)
        for i in tqdm(range(0, len(new_id_list), 1000)):
            ids = new_id_list[i : i + 1000]
            abstracts = NCBIQuery.id_abstract(ids)
            for id_, abstract in zip(ids, abstracts):
                if abstract is None or abstract == "":
                    continue
                output_file = os.path.join(args.output_dir, id_ + ".txt")
                with open(output_file, "w", encoding='utf-8') as f:
                    f.write(abstract)
    else:
        if args.id is not None:
            get_pmc([args.id], args.output_dir)
            get_scihub([args.id], args.output_dir)
            print("Trying to get papers using PubMed2PDF...")
            subprocess.run(
                [
                    "python3",
                    "-m",
                    "papertool.pubmed2pdf",
                    "pdf",
                    "--pmids",
                    args.id,
                    "--out",
                    args.output_dir,
                ],
                check=True,
            )
            get_sciencedirect([args.id], args.output_dir)
            get_elsevier_api([args.id], args.output_dir)
        else:
            with open(args.id_file, "r", encoding='utf-8') as f:
                id_list = f.read().splitlines()
            get_pmc(id_list, args.output_dir)
            get_scihub(id_list, args.output_dir)
            print("Trying to get papers using PubMed2PDF...")
            subprocess.run(
                [
                    "python3",
                    "-m",
                    "papertool.pubmed2pdf",
                    "pdf",
                    "--pmidsfile",
                    args.id_file,
                    "--out",
                    args.output_dir,
                ],
                check=True,
            )
            get_sciencedirect(id_list, args.output_dir)
            get_elsevier_api(id_list, args.output_dir)
