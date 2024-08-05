import time
import requests
import xml.etree.ElementTree as ET

# Telegram Bot configuration
BOT_TOKEN = '5925179620:AAELdC5OfDHXqvpBNEx5xEOjCzcPdY0isck'
CHAT_ID = '1640026631'
TG_API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

# List of RSS feeds to monitor
RSS_FEEDS = [
    'https://rsshub.app/youtube/user/@BonnieBlockchain',
    'https://rsshub.app/youtube/user/@qiudaoyu2024',
    'https://rsshub.app/youtube/user/@Ronnie-Analyze',
    'https://rsshub.app/youtube/user/@yiming3311',
    'https://rsshub.app/youtube/user/@RTAFinance',
    'https://rsshub.app/youtube/user/@sen888',
    'https://rsshub.app/youtube/user/@GiantCutie-CH',
    'https://rsshub.app/youtube/user/@YuchiTrader',
    'https://rsshub.app/youtube/user/@yttalkjun',
    'https://rsshub.app/youtube/user/@CKGOChannelShow',
    'https://rsshub.app/youtube/user/@ustvmoney100',
    'https://rsshub.app/youtube/user/@AVK.Money.Master',
    'https://rsshub.app/youtube/user/@UDTrading',
    'https://rsshub.app/youtube/user/@blockchaindailynews',
    'https://rsshub.app/youtube/user/@finanonym',
    'https://rsshub.app/youtube/user/@KoluniteVIP'
]

# Cache to store the latest RSS feed item for each URL
cache = {}

def fetch_feed(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def extract_latest_item(feed_content):
    # Parse XML and extract the latest item
    root = ET.fromstring(feed_content)
    latest_item = root.find('.//item')
    if latest_item is not None:
        title = latest_item.find('title').text
        link = latest_item.find('link').text
        pubDate = latest_item.find('pubDate').text
        return {
            'title': title,
            'link': link,
            'pubDate': pubDate
        }
    return None

def create_message(item):
    return (
        f"Title: {item['title']}\n"
        f"Link: {item['link']}\n"
        f"Published Date: {item['pubDate']}"
    )

def send_telegram_message(message):
    if len(message) > 4096:  # Telegram message limit
        message = message[:4096]
    
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(TG_API_URL, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print(f"Response text: {response.text}")
        print(f"Payload: {payload}")

def main():
    global cache
    while True:
        for url in RSS_FEEDS:
            try:
                feed_content = fetch_feed(url)
                latest_item = extract_latest_item(feed_content)

                if latest_item:
                    if url not in cache or cache[url] != latest_item['link']:
                        message = create_message(latest_item)
                        send_telegram_message(message)
                        cache[url] = latest_item['link']  # Update cache with the latest item's link

            except requests.exceptions.RequestException as e:
                print(f"Request failed for {url}: {e}")

        time.sleep(300)  # Wait for 5 minutes

if __name__ == '__main__':
    main()
