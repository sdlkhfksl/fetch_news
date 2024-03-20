import feedparser
import requests
import re

# 创建会话并设置用户代理
session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'

def reformat_url(url):
    """
    Change the url to a new format using regular expressions.
    """
    result = re.sub('https://cryptopanic.com/news/(\\d+)/.*', 'https://cryptopanic.com/news/click/\\1/', url)
    return result

def get_real_url(re_url):
    """
    Get the real url by using the redirection.
    """
    try:
        response = session.get(re_url, timeout=5)  # Use session to handle redirection
        response.raise_for_status()
        real_url = response.url
        return real_url
    except requests.exceptions.RequestException as e:
        print(f'Error fetching real URL: {e}')
        return None  # Return None if an error occurs

# 解析RSS feed
feed_url = 'https://cryptopanic.com/news/rss/'
feed = feedparser.parse(feed_url)

# 处理各个条目并采集新闻内容
for entry in feed.entries:
    if entry.link.startswith('https://cryptopanic.com/news/'):
        # 使用提供的函数对链接进行格式化和解析最终的URL
        formatted_url = reformat_url(entry.link)
        final_url = get_real_url(formatted_url)
        
        print(final_url)
