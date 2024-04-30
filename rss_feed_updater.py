import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from openai import OpenAI

# 环境变量中获取API密钥和基础URL
api_secret_key = os.getenv('OPENAI_API_KEY')  # GitHub Secret 名称使用大写字母
base_url = os.getenv('BASE_API_URL')          # GitHub Secret 名称使用大写字母

# 初始化OpenAI客户端
openai_client = OpenAI(api_key=api_secret_key, base_url=base_url)

# User-Agent 以避免HTTP 422错误
headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; YourBot/1.0; +http://yourwebsite.com/bot)'
}

# 文件路径
links_file_path = 'accumulated_links.txt'
rss_file_path = 'rss_feed.xml'
last_processed_link_file_path = 'last_processed_link.txt'

# ... 其余的函数不变 ...

# 获取新链接并处理的主体函数
def process_new_links_and_update_rss():
    new_links = get_new_links()
    rss_items_updated = []
    
    # 遍历新链接，并使用GPT-3处理链接指向的内容
    for url in new_links:
        # 通过Jina.ai 获取文本内容
        jina_response = requests.get(f'https://jina.ai/v1/{url}', headers=headers)  # 确保URL格式正确
        if jina_response.ok:
            # 使用OpenAI的GPT-3模型处理文本
            gpt_response = openai_client.Completion.create(
                engine="davinci",
                prompt=jina_response.text,
                max_tokens=150
            )
            # 添加处理后的内容到RSS项中，并保存新的RSS文件
            if gpt_response:
                processed_content = gpt_response.choices[0].text.strip()
                rss_items_updated.append(processed_content)
                update_rss_feed(processed_content, f"Article from {url}")
                # 更新最后处理过的链接
                with open(last_processed_link_file_path, 'w', encoding='utf-8') as f:
                    f.write(url)
                
    # 如果有更新，重写RSS文件保持最新50篇文章
    if rss_items_updated:
        update_rss_feed(rss_items_updated[-50:])  # 保留最新的50条记录

# 执行
if __name__ == "__main__":
    process_new_links_and_update_rss()
