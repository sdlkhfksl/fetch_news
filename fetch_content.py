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

# 定义重定向和格式化URL的函数
def reformat_url(url):
    result = re.sub('https://cryptopanic.com/news/(\\d+)/.*', 'https://cryptopanic.com/news/click/\\1/', url)
    return result

def get_real_url(re_url):
    try:
        response = session.get(re_url, timeout=5)
        response.raise_for_status()
        real_url = response.url
        # 如果URL已经处理过，返回None
        if real_url in processed_urls:
            return None
        # 否则，记录URL并返回
        processed_urls.add(real_url)
        return real_url
    except requests.exceptions.RequestException as e:
        print(f'Error fetching real URL: {e}')
        return None

def fetch_article_content(url):
    try:
        response = session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find_all('p')
        return ' '.join([p.get_text() for p in content])
    except requests.exceptions.RequestException as e:
        print(f'Error fetching article content: {e}')
        return 'Error fetching content'

# 解析RSS feed
feed_url = 'https://cryptopanic.com/news/rss/'
feed = feedparser.parse(feed_url)

# 存储抓取的文章内容
all_content = ''

# 检查是否是UTC时间0点
if datetime.utcnow().hour == 0:
    open('articles_content.txt', 'w').close()
    processed_urls.clear()

# 处理feed中的每条新闻
for entry in feed.entries:
    formatted_url = reformat_url(entry.link)
    final_url = get_real_url(formatted_url)
    if final_url:
        article_content = fetch_article_content(final_url)
        if article_content != 'Error fetching content':
            all_content += article_content + '\n\n---\n\n'

# 将新抓取的内容追加到现有文件中
with open('articles_content.txt', 'a') as file:
    file.write(all_content)
