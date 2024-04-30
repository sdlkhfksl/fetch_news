import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from openai import OpenAI

# 设置环境变量
API_SECRET_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("BASE_API_URL")

# 初始化OpenAI客户端
client = OpenAI(api_key=API_SECRET_KEY, base_url=BASE_URL)

# 定义请求头，模拟浏览器访问
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

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

def retrieve_text_from_jina(link):
    try:
        response = requests.get(f'https://r.jina.ai/{link}', headers=HEADERS)
        response.raise_for_status()
        return response.text
    except requests.HTTPError as e:
        print(f'HTTP error occurred: {e}')
    except Exception as e:
        print(f'An error occurred: {e}')
    return ""

def process_text_with_gpt(text):
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": text}],
        temperature=0,
        stream=True
    )
    for chunk in stream:
        if hasattr(chunk, 'choices'):
            choices = chunk.choices
            if len(choices) > 0:
                content = choices[0].message['content']
    return content

def append_to_rss(title, content):
    if not os.path.exists(RSS_FILE):
        root = ET.Element("rss", version="2.0")
        channel = ET.SubElement(root, "channel")
        
        # Assuming title and link are identical for simplicity.
        ET.SubElement(channel, "title").text = title
        ET.SubElement(channel, "link").text = title
        ET.SubElement(channel, "description").text = "RSS feed description"

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

    # Remove items to keep only the latest 30 entries.
    while len(channel.findall('item')) > 30:
        channel.remove(channel.findall('item')[-1])

    tree.write(RSS_FILE, encoding='utf-8', xml_declaration=True)

def workflow():
    new_links = get_new_links()
    for link in new_links:
        content = retrieve_text_from_jina(link)
        if content:
            processed_content = process_text_with_gpt(content)
            if processed_content:
                append_to_rss(f"New content from {link}", processed_content)
                update_last_processed_link(link)

if __name__ == "__main__":
    workflow()
