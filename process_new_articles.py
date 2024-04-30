import requests
import os
import time
from datetime import datetime

# 函数：获取 Markdown 内容，带重试机制和自定义 User-Agent
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
    return number + 1

# 特定文件路径的变量定义
links_file = 'accumulated_links.txt'
output_file = 'articles.md'
last_processed_file = 'last_processed_link.txt'

# 获取今天的编号
daily_number = calculate_daily_number(output_file)

# 尝试读取上次处理的最后一个链接
try:
    with open(last_processed_file, 'r') as file:
        last_processed_link = file.read().strip()
except FileNotFoundError:
    last_processed_link = None

# 读取全部链接，并找到需要处理的新链接
new_links = []
process_new_links = False
with open(links_file, 'r') as file:
    for line in file:
        line = line.strip()
        if not process_new_links and last_processed_link == line:
            process_new_links = True
            continue
        if process_new_links or last_processed_link is None:
            new_links.append(line)

# 处理新链接，并将新文章追加到文件
if new_links:
    # 读取当前所有文章并保留最新的文章到缓存列表
    articles_cache = []

    if os.path.exists(output_file):
        with open(output_file, 'r') as file:
            articles_cache = file.read().strip().split('\n## Article ')[-299:]  # 取最新的299篇文章（不包括当前即将写入的新文章）

    for url in new_links:
        content = fetch_markdown(url)
        if content:
            articles_cache.append(f"## Article {daily_number}\n" + content)
            daily_number += 1

    # 只写入最新的300篇文章（包括新文章）
    with open(output_file, 'w') as file:
        file.write('\n'.join(articles_cache[-300:]))

    # 更新最后处理的链接
    with open(last_processed_file, 'w') as file:
        file.write(new_links[-1])

print('Script execution completed.')
