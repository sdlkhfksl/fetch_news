import requests
import os
import time
from datetime import datetime, timedelta

# 函数：获取 Markdown 内容
def fetch_markdown(url):
    time.sleep(20)  # 预留 20 秒处理时间
    md_url = f"https://r.jina.ai/{url}"
    response = requests.get(md_url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error fetching {url}: Status code {response.status_code}")
        return None

# 函数：计算今天的文章编号
def calculate_daily_number(file_path):
    today = datetime.now().date()
    number = 1
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith(f"{today}"):
                    number += 1
    return number

# 读取现有链接和已处理的链接
accumulated_links = 'accumulated_links.txt'
processed_links = 'processed_links.txt'
output_articles = 'articles.md'

# 获取今天的编号
daily_number = calculate_daily_number(processed_links)

new_links = []
with open(accumulated_links, 'r') as f:
    curr_links = set(f.read().splitlines())

try:
    with open(processed_links, 'r') as f:
        old_links = set(f.read().splitlines())
    new_links = list(curr_links - old_links)
except FileNotFoundError:
    old_links = set()
    new_links = list(curr_links)

# 处理新链接
articles = []
if new_links:
    for url in new_links:
        content = fetch_markdown(url)
        if content:
            article_entry = f"## Article {daily_number}\n\n{content}\n\n"
            articles.append(article_entry)
            daily_number += 1

    # 将新增文章写入文件
    if articles:
        with open(output_articles, 'a') as f:
            f.write('\n\n'.join(articles))

    # 更新已处理链接文件
    with open(processed_links, 'w') as f:
        f.writelines('\n'.join(sorted(curr_links)))

# 保留最新300篇文章
try:
    with open(output_articles, 'r') as f:
        lines = f.readlines()

    with open(output_articles, 'w') as f:
        # Reverse to keep latest articles, then reverse again to correct order
        latest_300_articles = lines[-300:] if len(lines) > 300 else lines
        f.writelines(latest_300_articles)
except FileNotFoundError:
    pass
