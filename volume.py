import requests
import time
from collections import deque

# Telegram Bot Token and Chat ID
BOT_TOKEN = '7087052045:AAF3eJLHSvBGKtqqa2l_e7su_ESiteL8ai8'
CHAT_ID = '1640026631'

# Cryptocurrency IDs
CURRENCY_IDS = [
    'bitcoin',
    'dogecoin',
    'ethereum',
    'uniswap',
    'shiba-inu',
    'ripple',
    'binancecoin',
    'cardano',
    'worldcoin-wld',
    'solana',
    'avalanche-2',
    'polkadot',
    'the-open-network'
]

def get_volume(currency_id):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={currency_id}&vs_currencies=usd&include_24hr_vol=true'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if currency_id in data:
            return data[currency_id]['usd_24h_vol']
        else:
            print(f"Warning: {currency_id} not found in API response.")
            return None
    except requests.RequestException as e:
        print(f"Request error for {currency_id}: {e}")
        return None

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print(f"Sent message: {message}")
    except requests.RequestException as e:
        print(f"Error sending message: {e}")

def main():
    # Initialize volume data storage
    volume_data = {currency_id: deque(maxlen=2) for currency_id in CURRENCY_IDS}
    last_hour_check = time.time()

    while True:
        current_time = time.time()
        # Check if an hour has passed
        if current_time - last_hour_check >= 3600:
            for currency_id in CURRENCY_IDS:
                current_volume = get_volume(currency_id)
                if current_volume is not None:
                    volume_data[currency_id].append(current_volume)
                time.sleep(12)  # Wait for 12 seconds before the next request
            
            last_hour_check = current_time
        
        # Check volume changes
        for currency_id in CURRENCY_IDS:
            if len(volume_data[currency_id]) == 2:
                prev_hour_volume = volume_data[currency_id][0]
                curr_hour_volume = volume_data[currency_id][1]
                if curr_hour_volume > 2 * prev_hour_volume:
                    message = f"{currency_id.capitalize()}'s trading volume increased by more than 2x in the last hour."
                    send_telegram_message(message)
        
        # Wait for 5 minutes before the next check
        time.sleep(300)

if __name__ == '__main__':
    main()
