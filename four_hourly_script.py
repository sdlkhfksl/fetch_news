import requests
from readability import Document

def fetch_article_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    doc = Document(response.text)
    content = doc.summary(html_partial=True)
    return content if content else 'Article content not found or extraction failed.'

def fetch_and_write_article_contents(links_file_url, output_file, processed_links_file):
    # Get the list of URLs from the provided text file
    response = requests.get(links_file_url)
    if response.status_code == 200:
        # Split the content by new line to get individual URLs
        links = response.text.strip().split('\n')
        # Load already processed links
        try:
            with open(processed_links_file, 'r', encoding='utf-8') as f:
                processed_links = f.read().split('\n')
        except FileNotFoundError:
            processed_links = []

        # Write the contents to the output file
        with open(output_file, 'a', encoding='utf-8') as file, open(processed_links_file, 'a', encoding='utf-8') as processed_file:
            for url in links:
                # Skip the link if it has already been processed
                if url in processed_links:
                    continue
                print(f'Fetching content for: {url}')
                # Fetch the article content using the readability library
                article_content = fetch_article_content(url)
                # Write the content to the file
                file.write(article_content + '\n\n')
                # Add the url to processed links
                processed_file.write(url + '\n')
    else:
        print(f'Failed to retrieve links file. Status code: {response.status_code}')

# URL of the text file that contains the article links
links_file_url = 'https://raw.githubusercontent.com/sdlkhfksl/fetch_news/main/accumulated_links.txt'
# The output file where the article contents will be written
output_file = 'articles_content.txt'
# File to keep track of processed links
processed_links_file = 'processed_links.txt'

# Call the main function to start the process
fetch_and_write_article_contents(links_file_url, output_file, processed_links_file)
