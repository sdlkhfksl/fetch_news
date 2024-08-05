import requests
import time
from datetime import datetime

# YouTube Data API configuration
API_KEY = 'AIzaSyBm2mGvVGctQVFldy7ro7Smc8_vaY6QWhw'

# Telegram Bot configuration
BOT_TOKEN = '5925179620:AAELdC5OfDHXqvpBNEx5xEOjCzcPdY0isck'
CHAT_ID = '1640026631'
TG_API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

# List of channel IDs
CHANNEL_IDS = {
    'BonnieBlockchain': 'UCjlPLMYEsq0pjgLL1q24mSg',
    'qiudaoyu2024': 'UCdVv0fYE8HIAv7_dJmHSBlA',
    'Ronnie-Analyze': 'UCWRAtzLosbGhVt4-fDDSNPw',
    'yiming3311': 'UCxX-xxH01JZlc6Nbr5IcPAg',
    'RTAFinance': 'UCiwg-3pIDuI0KTWiH0BCRJA',
    'sen888': 'UCoZ94vl_voZvcQNInS_VL5w',
    'GiantCutie-CH': 'UCcHzySKWh5hyhZW4ZOXfgBA',
    'YuchiTrader': 'UCW1KHRAydlyBrX7nz7bz26g',
    'yttalkjun': 'UCRBrH2qS7yKGMNSmjnj8gcw',
    'CKGOChannelShow': 'UCH3ZKc_neKSAHkjeQga0cRQ',
    'ustvmoney100': 'UC_ObC9O0ZQ2FhW6u9_iFlZA',
    'AVK.Money.Master': 'UCZZpu8MLp_qdtRq9zizRsNg',
    'UDTrading': 'UC_n3pQXTrX2PtY9XJFmiM1Q',
    'blockchaindailynews': 'UCkPc41kPIJfMI0ZCTHqybYA',
    'finanonym': 'UCTXxEYFX7KklRzQ1Fuv89aQ',
    'KoluniteVIP': 'UCbZIP3-hbPOuaeHM0pWeM0w'
}

# To store the latest published date for each channel
last_pub_dates = {channel_id: None for channel_id in CHANNEL_IDS.values()}

def get_uploads_playlist_id(channel_id):
    """Get the uploads playlist ID for a given YouTube channel ID."""
    url = 'https://www.googleapis.com/youtube/v3/channels'
    params = {
        'part': 'contentDetails',
        'id': channel_id,
        'key': API_KEY
    }
    print(f"Fetching uploads playlist ID for channel ID: {channel_id}")
    response = requests.get(url, params=params)
    print(f"Response status code: {response.status_code}")
    response.raise_for_status()
    data = response.json()
    playlist_id = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    print(f"Uploads playlist ID: {playlist_id}")
    return playlist_id

def get_latest_videos(playlist_id, max_results=1):
    """Get the latest videos from a YouTube playlist."""
    url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    params = {
        'part': 'snippet',
        'playlistId': playlist_id,
        'maxResults': max_results,
        'key': API_KEY
    }
    print(f"Fetching latest videos from playlist ID: {playlist_id}")
    response = requests.get(url, params=params)
    print(f"Response status code: {response.status_code}")
    response.raise_for_status()
    return response.json()

def send_telegram_message(message):
    """Send a message to a Telegram chat."""
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    print(f"Sending message to Telegram: {message}")
    try:
        response = requests.post(TG_API_URL, json=payload)
        response.raise_for_status()
        print(f"Message sent successfully. Response status code: {response.status_code}")
        print(f"Response content: {response.json()}")
    except requests.exceptions.HTTPError as err:
        print(f"Failed to send message. Error: {err}")
        print(f"Response content: {response.text}")

def check_for_updates():
    global last_pub_dates
    for channel_name, channel_id in CHANNEL_IDS.items():
        print(f"Checking for updates for channel: {channel_name}")
        playlist_id = get_uploads_playlist_id(channel_id)
        latest_videos = get_latest_videos(playlist_id)
        
        if latest_videos['items']:
            latest_item = latest_videos['items'][0]
            title = latest_item['snippet']['title']
            video_id = latest_item['snippet']['resourceId']['videoId']
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            pub_date = latest_item['snippet']['publishedAt']
            
            print(f"Latest video title: {title}")
            print(f"Published date: {pub_date}")
            print(f"Video URL: {video_url}")

            # Update last_pub_date if it's the first run
            if last_pub_dates[channel_id] is None:
                last_pub_dates[channel_id] = pub_date
                print(f"First run for channel {channel_name}, updating last_pub_date.")
                continue
            
            # Check if the latest video is new
            if pub_date > last_pub_dates[channel_id]:
                last_pub_dates[channel_id] = pub_date
                message = f'New video on {channel_name}:\nTitle: {title}\nPublished at: {pub_date}\nURL: {video_url}'
                send_telegram_message(message)
            else:
                print(f"No new videos for channel {channel_name}.")
        else:
            print(f"No videos found in playlist for channel {channel_name}.")

def main():
    while True:
        print("Checking for updates...")
        check_for_updates()
        print("Sleeping for 5 minutes...")
        time.sleep(300)  # Sleep for 5 minutes

if __name__ == '__main__':
    main()
