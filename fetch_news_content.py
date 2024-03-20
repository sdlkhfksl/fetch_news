import feedparser
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

# 创建会话并设置用户代理
session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'

# 已经处理的URL集合
processed_urls = set()

def reformat_url(url):
    result = re.sub(r'https://cryptopanic.com/news/(\d+)/.*', r'https://cryptopanic.com/news/click/\1/', url)
    return result

def get_real_url(re_url):
    try:
        response = session.get(re_url, timeout=5)
        response.raise_for_status()
        real_url = response.url
        return real_url
    except requests.RequestException as e:
        print(f'Error fetching real URL: {e}')
        return None

def get_article_content(url):
    try:
        response = session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        # 根据文章的实际结构修改下行选择器
        article_section = soup.find('section', class_='article-content')
        text = article_section.get_text(separator=' ', strip=True) if article_section else ''
        return text
    except requests.RequestException as e:
        print(f'Error fetching article content: {e}')
        return ''

# 检查是否是UTC时间0点
current_hour_utc = datetime.utcnow().hour
if current_hour_utc == 0:
    open('articles_content.txt', 'w').close()
    processed_urls.clear()

# 提取每篇文章的链接并处理
feed_url = 'https://cryptopanic.com/news/rss/'
feed = feedparser.parse(feed_url)
for entry in feed.entries:
    article_url = reformat_url(entry.link)
    real_url = get_real_url(article_url)
    if real_url and real_url not in processed_urls:
        processed_urls.add(real_url)
        content = get_article_content(real_url)
        with open('articles_content.txt', 'a', encoding='utf-8') as file:
            file.write(content + '\n\n---\n\n')
