import os
import xml.etree.ElementTree as ET
from datetime import datetime
from openai import OpenAI
import time

# 设置API密钥、基础URL
API_SECRET_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("BASE_API_URL")

# 初始化OpenAI客户端
client = OpenAI(api_key=API_SECRET_KEY, base_url=BASE_URL)

# 文件路径
LINKS_FILE = 'accumulated_links.txt'
RSS_FILE = 'rss_feed.xml'
LAST_LINK_FILE = 'last_processed_link.txt'

def get_last_processed_link():
    try:
        with open(LAST_LINK_FILE, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""

def update_last_processed_link(link):
    with open(LAST_LINK_FILE, 'w') as file:
        file.write(link)

def get_new_links():
    last_processed_link = get_last_processed_link()
    with open(LINKS_FILE, 'r') as file:
        links = [line.strip() for line in file if line.strip()]
    
    if last_processed_link in links:
        return links[links.index(last_processed_link) + 1:]
    return links

def process_text_with_gpt(link):
    prefix = 'https://r.jina.ai/'
    newlink = prefix + link

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"content": newlink}],
        stream=True,
    )

    content = None
    for chunk in response:
        if hasattr(chunk, 'choices'):
            choices = chunk.choices
            if len(choices) > 0:
                content = choices[0].message['content']
                break
    return content

def append_to_rss(title, content):
    if not os.path.exists(RSS_FILE):
        root = ET.Element("rss", version="2.0")
        channel = ET.SubElement(root, "channel")
        ET.SubElement(channel, "title").text = title
        ET.SubElement(channel, "link").text = title
        ET.SubElement(channel, "description").text = f"Content from {title}"

        tree = ET.ElementTree(root)
    else:
        tree = ET.parse(RSS_FILE)
        root = tree.getroot()

    channel = root.find('channel')

    item = ET.Element('item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'description').text = content
    ET.SubElement(item, 'pubDate').text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    channel.insert(0, item)

    while len(channel.findall('item')) > 30:
        channel.remove(channel.findall('item')[-1])

    tree.write(RSS_FILE, encoding='utf-8', xml_declaration=True)

def process_links():
    new_links = get_new_links()
    for link in new_links:
        processed_content = process_text_with_gpt(link)
        # 控制请求频率
        time.sleep(20)
        if processed_content:
            append_to_rss(link, processed_content)
            update_last_processed_link(link)

if __name__ == "__main__":
    process_links()
