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

def get_price_and_volume(currency_id):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={currency_id}&vs_currencies=usd&include_24hr_vol=true'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if currency_id in data:
            return data[currency_id]['usd'], data[currency_id]['usd_24h_vol']
        else:
            print(f"Warning: {currency_id} not found in API response.")
            return None, None
    except requests.RequestException as e:
        print(f"Request error for {currency_id}: {e}")
        return None, None

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
    # Initialize price and volume data storage
    price_data = {currency_id: deque(maxlen=2) for currency_id in CURRENCY_IDS}
    volume_data = {currency_id: deque(maxlen=2) for currency_id in CURRENCY_IDS}
    last_hour_check = time.time()
    bitcoin_prev_level = None
    ethereum_prev_level = None

    while True:
        current_time = time.time()
        
        # Fetch data for all currencies
        for currency_id in CURRENCY_IDS:
            price, volume = get_price_and_volume(currency_id)
            if price is not None and volume is not None:
                price_data[currency_id].append(price)
                volume_data[currency_id].append(volume)
            time.sleep(12)  # Wait for 12 seconds before the next request
        
        # Check hourly volume changes
        if current_time - last_hour_check >= 3600:
            for currency_id in CURRENCY_IDS:
                if len(volume_data[currency_id]) == 2:
                    prev_hour_volume = volume_data[currency_id][0]
                    curr_hour_volume = volume_data[currency_id][1]
                    if curr_hour_volume > 2 * prev_hour_volume:
                        message = f"{currency_id.capitalize()}'s trading volume increased by more than 2x in the last hour."
                        send_telegram_message(message)
            last_hour_check = current_time
        
        # Check Bitcoin price changes
        if len(price_data['bitcoin']) == 2:
            bitcoin_current_price = price_data['bitcoin'][-1]
            bitcoin_prev_price = price_data['bitcoin'][0]
            bitcoin_current_level = int(bitcoin_current_price // 500) * 500
            bitcoin_prev_level = int(bitcoin_prev_price // 500) * 500
            if bitcoin_current_level != bitcoin_prev_level:
                direction = "broke through" if bitcoin_current_price > bitcoin_prev_price else "dropped below"
                message = f"Bitcoin's price {direction} ${bitcoin_current_level}. Current price: ${bitcoin_current_price}."
                send_telegram_message(message)
        
        # Check Ethereum price changes
        if len(price_data['ethereum']) == 2:
            ethereum_current_price = price_data['ethereum'][-1]
            ethereum_prev_price = price_data['ethereum'][0]
            ethereum_current_level = int(ethereum_current_price // 500) * 500
            ethereum_prev_level = int(ethereum_prev_price // 500) * 500
            if ethereum_current_level != ethereum_prev_level:
                direction = "broke through" if ethereum_current_price > ethereum_prev_price else "dropped below"
                message = f"Ethereum's price {direction} ${ethereum_current_level}. Current price: ${ethereum_current_price}."
                send_telegram_message(message)

        # Wait for 5 minutes before the next check
        time.sleep(300)

if __name__ == '__main__':
    main()
