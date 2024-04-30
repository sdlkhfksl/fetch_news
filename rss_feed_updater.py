import os
import requests
import xml.etree.ElementTree as ET
from openai import ChatCompletion

# 从环境变量获取API密钥和基础URL
API_SECRET_KEY = os.getenv('OPENAI_API_KEY')
BASE_URL = os.getenv('BASE_API_URL')

# 初始化OpenAI客户端
client = ChatCompletion(api_key=API_SECRET_KEY, base_url=BASE_URL)

# User-Agent避免被网站拒绝服务
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# 文件路径
links_file = 'accumulated_links.txt'
rss_file = 'rss_feed.xml'
last_link_file = 'last_processed_link.txt'

# 获取最后处理的链接
def get_last_processed_link():
    try:
        with open(last_link_file, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""

# 保存最后处理的链接
def save_last_processed_link(url):
    with open(last_link_file, 'w') as file:
        file.write(url)

# 更新RSS Feed文件
def update_rss_feed(new_articles):
    root = ET.Element('rss', version='2.0')
    channel = ET.SubElement(root, 'channel')

    for article in new_articles:
        item = ET.SubElement(channel, 'item')
        title = ET.SubElement(item, 'title')
        description = ET.SubElement(item, 'description')
        title.text = article['title']
        description.text = article['content']

    tree = ET.ElementTree(root)
    tree.write(rss_file, encoding='utf-8', xml_declaration=True)

# 处理链接并更新RSS
def process_links():
    last_processed_link = get_last_processed_link()
    
    # 从文件中获取所有链接
    with open(links_file, 'r') as file:
        links = [link.strip() for link in file.readlines()]
    
    # 如果文件中有最后处理的链接，从下一个链接开始处理
    if last_processed_link in links:
        last_index = links.index(last_processed_link) + 1
        links = links[last_index:]
    
    new_articles = []
    for url in links:
        # 通过Jina.ai访问每个新链接获取文本内容
        response = requests.get(url, headers=HEADERS)
        if response.ok:
            text_content = response.text  # 文本内容
            # 发送文本给GPT API进行处理
            stream = client.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": text_content}],
                stream=True,
            )
            
            processed_content = ''
            for chunk in stream:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    processed_content = chunk['choices'][0]['message']['content']
                    break
            
            new_articles.append({"title": f"Processed Article from {url}", "content": processed_content})
            save_last_processed_link(url)
    
    # 更新 RSS 文件，只保留最新的50篇文章
    if new_articles:
        update_rss_feed(new_articles[-50:])

if __name__ == '__main__':
    process_links()
