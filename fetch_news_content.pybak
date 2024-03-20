import feedparser
import requests
import re
import time
from readability import Document
from datetime import datetime

# 定义全局变量以存储已处理过的 URL
processed_urls = set()

# 创建会话并设置用户代理
session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0.1) Gecko/20100101 Firefox/15.0.1'

# 定义用于重格式化 URL 的函数
def reformat_url(url):
    result = re.sub(r'https://cryptopanic.com/news/(\d+)/.*', r'https://cryptopanic.com/news/click/\1/', url)
    return result

# 定义函数以添加延迟并返回最终跳转后的 URL
def get_real_url(re_url):
    time.sleep(10)  # 在请求之前添加10秒的延迟
    try:
        response = session.get(re_url, timeout=5)
        response.raise_for_status()
        real_url = response.url
        return real_url
    except requests.exceptions.RequestException as e:
        print(f'Error fetching real URL: {e}')
        return None

# 使用 readability 替换 BeautifulSoup 来获取文章内容
def fetch_article_content(url):
    response = session.get(url)
    doc = Document(response.text)
    content = doc.summary(html_partial=True)  # 获取文档摘要
    if content:
        return content
    return 'Article content not found or extraction selector incorrect.'

# 清空内容文件和已处理 URLs 集合若当前为 UTC 时间0点
if datetime.utcnow().hour == 0:
    with open('articles_content.txt', 'w') as file:
        file.truncate(0)
    processed_urls.clear()

# 解析 RSS feed
feed_url = 'https://cryptopanic.com/news/rss/'
feed = feedparser.parse(feed_url)

# 逐个处理 feed 中的每个条目
for entry in feed.entries:
    reformatted_url = reformat_url(entry.link)
    if reformatted_url not in processed_urls:
        real_url = get_real_url(reformatted_url)
        if real_url and real_url not in processed_urls:
            processed_urls.add(real_url)
            content = fetch_article_content(real_url)
            with open('articles_content.txt', 'a', encoding='utf-8') as file:
                file.write(content + '\\n\\n---\\n\\n')
