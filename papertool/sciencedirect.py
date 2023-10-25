from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
import time
import random
from random import uniform
import urllib.request
import requests
from tqdm import tqdm
import os


def pmid_to_url(pmid):
    pmid = str(pmid)
    base_url = "https://pubmed.ncbi.nlm.nih.gov/"
    url = base_url + pmid
    return url

def sd_get_text(driver):
    element = driver.find_element(By.TAG_NAME, 'article')  # _by_tag_name('p')
    texts = " ".join(element.text.split('\n'))
    return texts

def jbc_get_text(driver):
    tmp1 = driver.find_element(By.ID, 'articleHeader') 
    tmp2 = driver.find_element(By.CLASS_NAME, 'article__body')
    text = tmp1.text + tmp2.text
    texts = " ".join(text.split('\n'))
    return texts

def get_sciencedirect(pmid_list, output_dir):
    print("Trying to get papers from ScienceDirect...")

    ### initiate driver
    url = 'https://www.sciencedirect.com/science/article/pii/S1896112618300890?via%3Dihub'

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.138 Safari/537.36 Edg/114.0.1823.41"
    # user_agent = "Twitterbot"
    service = Service(executable_path='/usr/bin/chromedriver')
    options = webdriver.ChromeOptions()
    # options.add_experimental_option('excludeSwitches', ['enable-automation'])
    # options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument("--remote-debugging-port=8888") 
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    checked = {}

    paper_texts = {}
    cnt_nolink, cnt_jbc_pdf, cnt_htmlerror, cnt_pdf, cnt_new = 0, 0, 0, 0, 0
    for pmid in tqdm(pmid_list):
        filename = os.path.join(output_dir, f"{pmid}.txt")
        filename_pdf = os.path.join(output_dir, f"{pmid}.pdf")
        filename_html = os.path.join(output_dir, f"{pmid}.html")
        if os.path.exists(filename) or os.path.exists(filename_pdf) or os.path.exists(filename_html) or (pmid in checked.keys() and 'JBC' not in checked[pmid]) or pmid in paper_texts.keys():
            continue
        cnt_new +=1 
        url = pmid_to_url(pmid)
        driver.get(url)
        try:
            link = driver.find_element(By.XPATH, '//div[@class="full-text-links-list"]/a').get_attribute('href')
            time.sleep(uniform(0,1))
            driver.get(link)
            time.sleep(uniform(2,3))
            curr_link = driver.current_url
        except:
            # print('No link', pmid)
            cnt_nolink +=1
            checked[pmid] = 'No link'
            continue
        if 'pdf' not in curr_link:
            if 'sciencedirect' in curr_link:    # case 1
                try:
                    paper_texts[pmid] = sd_get_text(driver)
                except:                         
                    print('SD html to text error', pmid)
                    cnt_htmlerror +=1
                    checked[pmid] = 'SD html to text error' 
                    continue       
            elif 'jbc' in curr_link:            # case 2
                try:
                    paper_texts[pmid] = jbc_get_text(driver)
                except:
                    print('JBC html to text error', pmid)
                    cnt_htmlerror +=1
                    checked[pmid] = 'JBC html to text error' 
                    continue
            else:  
                try:                            # case 3
                    element = driver.find_element(By.TAG_NAME, 'article')  
                    texts = " ".join(element.text.split('\n'))
                    paper_texts[pmid] = texts
                except:
                    try:                        # case 4
                        element = driver.find_element(By.XPATH, '//*[@id="ContentColumn"]')  
                        texts = " ".join(element.text.split('\n'))    
                        paper_texts[pmid] = texts
                    except:
                        # print('HTML Error Found', pmid)
                        cnt_htmlerror +=1
                        checked[pmid] = 'HTML Error Found' 
                        continue
            if pmid in paper_texts:
                with open(filename, 'w') as file:
                    file.write(paper_texts[pmid])

        else: 
            # print('Directs to a PDF', pmid)
            cnt_pdf +=1
            checked[pmid] = 'Directs to a PDF'
    driver.quit()