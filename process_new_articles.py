import requests
import os
import time
from datetime import datetime

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

links_file = 'accumulated_links.txt'
output_file = 'articles.md'
last_processed_file = 'last_processed_link.txt'

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

# 处理新链接
articles = []
for url in new_links:
    content = fetch_markdown(url)
    if content:
        articles.append(f"## Article {daily_number}\n" + content)
        daily_number += 1

# 将新增文章追加到文件
if articles:
    with open(output_file, 'a') as file:
        file.write('\n\n'.join(articles) + '\n\n')

# 更新最后处理的链接
if new_links:
    with open(last_processed_file, 'w') as file:
        file.write(new_links[-1])

print('Script execution completed.')
