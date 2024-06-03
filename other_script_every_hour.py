import requests
from readability import Document
import re
from html.parser import HTMLParser
from collections import deque
from datetime import datetime
import xml.etree.cElementTree as ET

# A simple HTML parser to remove HTML tags and retrieve text content
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = deque()

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return ''.join(self.text)

# Function to fetch and parse article, then clean HTML tags using MLStripper
def fetch_article_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            doc = Document(response.text)
            s = MLStripper()
            s.feed(doc.title())
            title = s.get_data()
            s = MLStripper()
            s.feed(doc.summary())
            content = s.get_data()
            # Return a dictionary of the clean title and content
            return {'title': title, 'content': content, 'url': url}
    except requests.RequestException:
        return None

# Function to add articles to RSS XML 
def append_to_rss(root, article):
    item = ET.SubElement(root, 'item')
    title = ET.SubElement(item, 'title')
    title.text = article['title']

    link = ET.SubElement(item, 'link')
    link.text = article['url']

    description = ET.SubElement(item, 'description')
    description.text = article['content']

    pub_date = ET.SubElement(item, 'pubDate')
    pub_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

# Fetch and write article contents to an XML file
def fetch_and_write_articles_to_rss(links_url, output_rss_file):
    response = requests.get(links_url)
    links = response.text.strip().split('\n')

    # Create the root element 'rss'
    root = ET.Element('rss', version="2.0")
    channel = ET.SubElement(root, 'channel')
    
    for url in links:
        article = fetch_article_content(url)
        if article:
            append_to_rss(channel, article)
    
    tree = ET.ElementTree(root)
    tree.write(output_rss_file, encoding='utf-8', xml_declaration=True)

# URLs file containing article links
links_url = 'https://raw.githubusercontent.com/sdlkhfksl/fetch_news/main/accumulated_links.txt'
# Output RSS file where articles content will be written in XML format
output_rss_file = 'articles_rss.xml'

# Run the function to start the process
fetch_and_write_articles_to_rss(links_url, output_rss_file)
