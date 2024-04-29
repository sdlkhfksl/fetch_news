import requests
import os
import time
from datetime import datetime

# 函数：获取 Markdown 内容，带重试机制和自定义User-Agent
def fetch_markdown(url):
    time.sleep(20)  # 预留 20 秒处理时间
    md_url = f"https://r.jina.ai/{url}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    try:
        response = requests.get(md_url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error fetching {url}: Status code {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

# 函数：计算今天的文章编号
def calculate_daily_number(file_path):
    today = datetime.now().strftime('%Y-%m-%d')
    number = 0
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if today in line:
                    number += 1
    except FileNotFoundError:
        pass
    return number + 1  # 开始新的编号

# 读取现有链接和已处理的链接
accumulated_links_file = 'accumulated_links.txt'
processed_links_file = 'processed_links.txt'
output_articles_file = 'articles.md'

# 获取今天的编号
daily_number = calculate_daily_number(processed_links_file)

new_links = []
try:
    with open(accumulated_links_file, 'r') as f:
        accumulated_links = set(f.read().strip().splitlines())
    with open(processed_links_file, 'r') as f:
        processed_links = set(f.read().strip().splitlines())
    new_links = list(accumulated_links - processed_links)
except FileNotFoundError:
    # 如果文件不存在，假设所有链接都是新的
    new_links = list(accumulated_links)

# 处理新链接
articles = []
if new_links:
    for url in new_links:
        content = fetch_markdown(url)
        if content:
            articles.append(f"## Article {daily_number}\n" + content)
            daily_number += 1

# 将新增文章和已处理链接写入文件
if articles:
    with open(output_articles_file, 'a') as file:
        file.write('\n\n'.join(articles) + '\n\n')

with open(processed_links_file, 'w') as file:
    file.writelines('\n'.join(sorted(accumulated_links)))

# 保留最新300篇文章
try:
    with open(output_articles_file, 'r') as file:
        current_articles = file.read().strip().split('\n\n## Article ')

    # 如果超过300篇，只保留最新的300篇
    with open(output_articles_file, 'w') as file:
        if len(current_articles) > 300:
            current_articles = current_articles[-300:]
        file.write('\n\n' .join(current_articles).strip())
except FileNotFoundError:
    pass

print('Script execution completed.')
