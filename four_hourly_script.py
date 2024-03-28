import os
import datetime
from readability import Document
import requests
from html.parser import HTMLParser
from collections import deque  # 导入deque类

# A simple HTML parser to remove HTML tags and retrieve text content
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return "".join(self.text)

# Use readability to fetch and parse article, then use MLStripper to clean HTML tags.
def fetch_article_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        doc = Document(response.text)
        # Use MLStripper to remove HTML tags
        s = MLStripper()
        s.feed(doc.title())
        title = s.get_data()
        s = MLStripper()
        s.feed(doc.summary())
        content = s.get_data()
        # Combine the title and the content
        formatted_content = title + "\n\n" + content
        return formatted_content
    else:
        return 'Article content not found or extraction failed.'

# Main function to fetch and write article contents
def fetch_and_write_article_contents(links_file_url, output_file, processed_links_file):
    response = requests.get(links_file_url)
    if response.status_code == 200:
        links = response.text.strip().split('\n')
        try:
            with open(processed_links_file, 'r', encoding='utf-8') as f:
                processed_links = deque(f.read().split('\n'), maxlen=300)
        except FileNotFoundError:
            processed_links = deque(maxlen=300)
        with open(output_file, 'w', encoding='utf-8') as file:  # Open the file in write mode to overwrite existing content
            for url in links:
                if url not in processed_links:
                    print(f'Fetching content for: {url}')
                    content = fetch_article_content(url)
                    processed_links.append(url)  # Add the URL to the deque
                    file.write(content + '\n\n----------------\n\n')
            # Write only the last 100 processed links back to the file
            with open(processed_links_file, 'w', encoding='utf-8') as processed_file:
                for link in processed_links:
                    processed_file.write(link + '\n')
    else:
        print(f'Failed to retrieve links file. Status code: {response.status_code}')

# URLs file containing article links
links_file_url = 'https://raw.githubusercontent.com/sdlkhfksl/fetch_news/main/accumulated_links.txt'
# Output file where article contents will be written
output_file = 'articles_content.txt'
# File to keep track of processed links
processed_links_file = 'processed_links.txt'

# Start the processing
fetch_and_write_article_contents(links_file_url, output_file, processed_links_file)
