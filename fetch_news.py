import feedparser
import requests
import re
import time
from collections import deque  # 导入deque类，用于存储固定数量的链接

# 创建会话并设置用户代理
session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'

# 定义重定向和格式化URL的函数
def reformat_url(url):
    result = re.sub('https://cryptopanic.com/news/(\\d+)/.*', 'https://cryptopanic.com/news/click/\\1/', url)
    return result

def get_real_url(re_url):
    time.sleep(10)  # 添加的延时
    try:
        response = session.get(re_url, timeout=5)
        response.raise_for_status()
        return response.url
    except requests.exceptions.RequestException as e:
        print(f'Error fetching real URL: {e}')
        return None

# 读取累积的链接或初始化一个空deque，最多存储100条链接
try:
    with open('accumulated_links.txt', 'r') as file:
        accumulated_links = deque(file.read().splitlines(), maxlen=100)
except FileNotFoundError:
    accumulated_links = deque(maxlen=300)

# 解析RSS feed
feed_url = 'https://cryptopanic.com/news/rss/'
feed = feedparser.parse(feed_url)

for entry in feed.entries:
    formatted_url = reformat_url(entry.link)
    final_url = get_real_url(formatted_url)
    
    if final_url and final_url not in accumulated_links:
        accumulated_links.append(final_url)  # 添加新链接到deque中

# 将新链接写入文件，只保留最近的100条
with open('accumulated_links.txt', 'w') as file:
    for link in list(accumulated_links)[-300:]:  # 只写入最近的100条链接
        file.write(link + '\n')

# 打印所有链接，可选操作
for link in accumulated_links:
    print(link)
