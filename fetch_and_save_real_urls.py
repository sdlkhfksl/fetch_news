import os
import requests
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from collections import deque

# Configuration
CRYPTOPANIC_API_TOKEN = "29fbfbbfbf3228ccdf295f99b96eeed102d62902"

# Logging Configuration
log_file = "./fetch_and_save_real_urls.log"  # Log file in root directory
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s', handlers=[logging.FileHandler(log_file), logging.StreamHandler()])

# Function to extract real URL using Selenium and BeautifulSoup
def extract_real_url_with_selenium(page_url):
    chrome_service = Service(ChromeDriverManager().install())
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1200")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    
    try:
        driver.get(page_url)
        time.sleep(5)  # Adjust wait time as needed
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        a_tag = soup.select_one("h1.post-title > a[rel][target='_blank']")
        if a_tag and 'href' in a_tag.attrs:
            return a_tag['href']
        else:
            logging.warning(f"No <a> tag found on page for URL: {page_url}")
    except Exception as e:
        logging.error(f'Error in Selenium while fetching URL {page_url}: {e}')
    finally:
        driver.quit()
    return None

# Function to fetch new article links from CryptoPanic
def fetch_new_article_links(api_token):
    url = f'https://cryptopanic.com/api/v1/posts/?auth_token={api_token}&public=true'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return [post['url'] for post in data['results'] if 'url' in post]

# Directory to store real URLs
output_file = "./real_urls.txt"

# Load existing URLs to maintain the latest 50 links
url_queue = deque(maxlen=50)
try:
    with open(output_file, "r") as file:
        for line in file:
            url_queue.append(line.strip())
except FileNotFoundError:
    logging.info(f"{output_file} file not found, starting with an empty deque")

# Fetch new article links
new_links = fetch_new_article_links(CRYPTOPANIC_API_TOKEN)

# Process each link to get the real URL and save it to file
for url in new_links:
    real_url = extract_real_url_with_selenium(url)
    if real_url and real_url not in url_queue:
        url_queue.append(real_url)
        logging.info(f"Processed URL: {real_url}")
    else:
        if not real_url:
            logging.warning(f"Failed to process URL: {url}")
        else:
            logging.info(f"URL already in queue: {real_url}")
    time.sleep(10)  # Rate-limit our requests

# Save the latest 20 URLs back to the file
try:
    with open(output_file, "w") as file:
        for url in url_queue:
            file.write(url + "\n")
    logging.info(f"Successfully wrote to {output_file}")
except Exception as e:
    logging.error(f"Failed to write to {output_file}: {e}")
