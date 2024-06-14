import feedparser
import requests
import time
from collections import deque
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Helper Functions
def get_real_url(url):
    """Retrieve the final URL using Selenium."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(5)  # 等待页面加载完成
        real_url = driver.current_url
        return real_url
    except Exception as e:
        print(f'Error fetching real URL: {e}')
        return None
    finally:
        driver.quit()

# 读取累积的链接或初始化一个空deque，最多存储30条链接
try:
    with open('accumulated_links.txt', 'r') as file:
        accumulated_links = deque(file.read().splitlines(), maxlen=30)
except FileNotFoundError:
    accumulated_links = deque(maxlen=30)

# 解析RSS feed
feed_url = 'https://cryptopanic.com/news/rss/'
feed = feedparser.parse(feed_url)

for entry in feed.entries:
    final_url = get_real_url(entry.link)
    
    if final_url and final_url not in accumulated_links:
        accumulated_links.append(final_url)  # 添加新链接到deque中

# 将新链接写入文件，只保留最近的30条
with open('accumulated_links.txt', 'w') as file:
    for link in accumulated_links:
        file.write(link + '\n')

# 打印所有链接，可选操作
for link in accumulated_links:
    print(link)
