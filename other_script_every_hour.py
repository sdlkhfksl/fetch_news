import requests
from readability import Document
from html.parser import HTMLParser
from collections import deque

# A simple HTML parser to remove HTML tags and retrieve text content
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

# Function to fetch and extract article content
def fetch_article_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        doc = Document(response.text)
        title = doc.title()
        s = MLStripper()
        s.feed(doc.summary())
        content = s.get_data()
        formatted_content = title + "\n\n" + content
        return formatted_content
    else:
        return 'Article content not found or extraction failed.'

# Main function to fetch and write article contents
def fetch_and_write_article_contents(links_file_url, output_file, processed_links_file):
    response = requests.get(links_file_url)
    if response.status_code == 200:
        links = response.text.strip().split('\n')
        processed_links = deque(maxlen=300)
        existing_contents = deque(maxlen=300)
        
        try:
            with open(processed_links_file, 'r', encoding='utf-8') as f:
                processed_links.extend(f.read().split('\n'))
        except FileNotFoundError:
            pass
        
        try:
            with open(output_file, 'r', encoding='utf-8') as file:
                existing_contents.extend(file.read().split('\n\n----------------\n\n'))
        except FileNotFoundError:
            pass
        
        with open(output_file, 'w', encoding='utf-8') as file, open(processed_links_file, 'w', encoding='utf-8') as processed_file:
            for url in links:
                if url not in processed_links:
                    print(f'Fetching content for: {url}')
                    content = fetch_article_content(url)
                    if content != 'Article content not found or extraction failed.':
                        existing_contents.append(content)
                        processed_links.append(url)
            
            # Write the updated contents back to the file
            file.write('\n\n----------------\n\n'.join(list(existing_contents)[-300:]))
            # Update the processed links file
            processed_file.write('\n'.join(list(processed_links)[-300:]))
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
