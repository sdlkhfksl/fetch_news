import feedparser
import requests
import re
import time  # 这里添加了对time模块的导入
from datetime import datetime

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

# 读取累积的链接或初始化一个空集合
try:
    with open('accumulated_links.txt', 'r') as file:
        accumulated_links = set(file.read().splitlines())
except FileNotFoundError:
    accumulated_links = set()

# 解析RSS feed
feed_url = 'https://cryptopanic.com/news/rss/'
feed = feedparser.parse(feed_url)

for entry in feed.entries:
    formatted_url = reformat_url(entry.link)
    final_url = get_real_url(formatted_url)
    
    if final_url and final_url not in accumulated_links:
        accumulated_links.add(final_url)  # 添加新链接到集合中

# 将新链接写入文件
with open('accumulated_links.txt', 'w') as file:
    for link in accumulated_links:
        file.write(link + '\n')

# 打印所有链接，可选操作
for link in accumulated_links:
    print(link)

# 如果当前是UTC时间0点，则清空accumulated_links.txt文件
if datetime.utcnow().hour == 0 and datetime.utcnow().minute < 5:  # 修改为UTC时间并增加5分钟的缓冲
    open('accumulated_links.txt', 'w').close()
