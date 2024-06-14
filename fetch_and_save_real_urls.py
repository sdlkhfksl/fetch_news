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
CRYPTOPANIC_API_TOKEN = os.getenv("CRYPTOPANIC_API_TOKEN", "29fbfbbfbf3228ccdf295f99b96eeed102d62902")

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

# Directory to store URLs
raw_urls_file = "./raw_urls.txt"
real_urls_file = "./real_urls.txt"

# Load existing raw URLs to maintain the latest 50 links
raw_url_queue = deque(maxlen=50)
try:
    with open(raw_urls_file, "r") as file:
        for line in file:
            raw_url_queue.append(line.strip())
except FileNotFoundError:
    logging.info(f"{raw_urls_file} file not found, starting with an empty deque")

# Load existing real URLs to maintain the latest 50 links
real_url_queue = deque(maxlen=50)
try:
    with open(real_urls_file, "r") as file:
        for line in file:
            real_url_queue.append(line.strip())
except FileNotFoundError:
    logging.info(f"{real_urls_file} file not found, starting with an empty deque")

# Fetch new article links
new_links = fetch_new_article_links(CRYPTOPANIC_API_TOKEN)

# Process each link to get the real URL and save it to file
new_raw_urls = []
for url in new_links:
    if url not in raw_url_queue:
        new_raw_urls.append(url)
        raw_url_queue.append(url)

        real_url = extract_real_url_with_selenium(url)
        if real_url and real_url not in real_url_queue:
            real_url_queue.append(real_url)
            logging.info(f"Processed and stored URL: {real_url}")
        else:
            logging.warning(f"Failed to process URL: {url}")
        time.sleep(10)  # Rate-limit our requests
    else:
        logging.info(f"URL {url} has already been processed and stored")

# Save the latest 50 raw URLs to file
try:
    with open(raw_urls_file, "w") as file:
        for url in raw_url_queue:
            file.write(url + "\n")
    logging.info(f"Successfully wrote to {raw_urls_file}")
except Exception as e:
    logging.error(f"Failed to write to {raw_urls_file}: {e}")

# Save the latest 50 real URLs to file
try:
    with open(real_urls_file, "w") as file:
        for url in real_url_queue:
            file.write(url + "\n")
    logging.info(f"Successfully wrote to {real_urls_file}")
except Exception as e:
    logging.error(f"Failed to write to {real_urls_file}: {e}")

logging.info(f"Completed processing. Stored URLs count: {len(real_url_queue)}")
