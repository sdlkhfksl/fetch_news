import feedparser
import requests
import re
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

# 清空链接文件，这将在工作流中配置
if datetime.now().hour == 0:  # 假设在UTC时间0点执行清空操作
    open('accumulated_links.txt', 'w').close()
