import os
import feedparser
import requests
import re
import time
from readability import Document
from datetime import datetime

def reformat_url(url):
    result = re.sub(r'https://cryptopanic.com/news/(\d+)/.*', r'https://cryptopanic.com/news/click/\1/', url)
    return result

def get_real_url(re_url):
    time.sleep(10)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0;Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    response = requests.get(re_url, headers = headers, allow_redirects=True, timeout=5)
    response.raise_for_status()
    real_url = response.url
    return real_url

def fetch_article_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0;Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    response = requests.get(url, headers = headers)
    doc = Document(response.text)
    content = doc.summary(html_partial=True)
    if content:
        return content
    return 'Article content not found or extraction selector incorrect.'


session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0;Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
processed_urls = set()

if datetime.utcnow().hour == 0:
    with open('articles_content.txt', 'w') as file:
        file.truncate(0)
    processed_urls.clear()


feed_url = 'https://cryptopanic.com/news/rss/'
feed = feedparser.parse(feed_url)


for entry in feed.entries:
    reformatted_url = reformat_url(entry.link)
    if reformatted_url not in processed_urls:
        real_url = get_real_url(reformatted_url)
        if real_url and real_url not in processed_urls:
            processed_urls.add(real_url)
            content = fetch_article_content(real_url)
            with open('articles_content.txt', 'a', encoding='utf-8') as file:
                file.write(content + '\n\n---\n\n')
