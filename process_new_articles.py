import requests
import os
import time
from xml.etree.ElementTree import Element, SubElement, ElementTree
from datetime import datetime

# 函数：获取 Markdown 内容，带重试机制和自定义 User-Agent
def fetch_markdown(url):
    md_url = f"https://r.jina.ai/{url}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    try:
        response = requests.get(md_url, headers=headers)
        time.sleep(20)  # 预留 20 秒处理时间
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error fetching {url}: Status code {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

# 把 Markdown 文本追加到 RSS XML 文件中
def append_to_rss(url, content):
    rss_file = 'news_feed.xml'
    
    # 创建或读取 XML 树
    if os.path.exists(rss_file):
        tree = ElementTree()
        tree.parse(rss_file)
        root = tree.getroot()
        channel = root.find('channel')
    else:
        root = Element('rss')
        root.set('version', '2.0')
        channel = SubElement(root, 'channel')
        SubElement(channel, 'title').text = "News Feed"
        SubElement(channel, 'description').text = "Latest news updates"
        SubElement(channel, 'link').text = "https://example.com" # 你的新闻链接网站
        
    # 添加新文章
    item = SubElement(channel, 'item')
    SubElement(item, 'title').text = f"News Article {len(channel.findall('item')) + 1}" 
    SubElement(item, 'description').text = content
    SubElement(item, 'pubDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    SubElement(item, 'link').text = url
    
    # 保持文章数量不超过50篇
    while len(channel.findall('item')) > 50:
        channel.remove(channel.findall('item')[0])

    tree = ElementTree(root)
    tree.write(rss_file, encoding='UTF-8', xml_declaration=True)

# 特定文件路径的变量定义
links_file = 'accumulated_links.txt'
last_processed_file = 'last_processed_link.txt'

# 读取上次处理的最后一个链接
last_processed_link = ""
if os.path.exists(last_processed_file):
    with open(last_processed_file, 'r') as file:
        last_processed_link = file.read().strip()

# 读取全部链接，并找到需要处理的新增链接
new_links = []
process_new_links = False
with open(links_file, 'r') as file:
    for line in file:
        line = line.strip()
        if not process_new_links and last_processed_link == line:
            process_new_links = True
            continue
        if process_new_links or last_processed_link == "":
            new_links.append(line)

# 处理新链接，并将新文章追加到文件
for url in new_links:
    content = fetch_markdown(url)
    if content:
        append_to_rss(url, content)
        last_processed_link = url
        # 更新最后处理的链接
        with open(last_processed_file, 'w') as file:
            file.write(last_processed_link)

print('Script execution completed.')
