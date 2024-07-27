import requests
import time
from collections import deque

# Telegram Bot Token and Chat ID
BOT_TOKEN = '7087052045:AAF3eJLHSvBGKtqqa2l_e7su_ESiteL8ai8'
CHAT_ID = '1640026631'

# Cryptocurrency IDs
CURRENCY_IDS = ['bitcoin', 'ethereum', 'uniswap', 'shiba-inu', 'ripple', 'binancecoin', 'cardano', 'worldcoin-wld', 'solana', 'avalanche-2', 'polkadot', 'the-open-network']

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

def calculate_change(current, previous):
    return (current - previous) / previous * 100 if previous != 0 else 0

def main():
    price_data = {currency_id: deque(maxlen=3) for currency_id in CURRENCY_IDS}
    volume_data = {currency_id: deque(maxlen=3) for currency_id in CURRENCY_IDS}
    
    while True:
        start_time = time.time()
        
        # Fetch price and volume for each cryptocurrency
        for currency_id in CURRENCY_IDS:
            price, volume = get_price_and_volume(currency_id)
            if price is not None and volume is not None:
                price_data[currency_id].append(price)
                volume_data[currency_id].append(volume)
            time.sleep(12)  # Wait for 12 seconds before fetching the next data
        
        # Check price changes
        if len(price_data['bitcoin']) == 3:
            bitcoin_price_change = calculate_change(price_data['bitcoin'][-1], price_data['bitcoin'][0])
            
            other_price_changes = [calculate_change(price_data[currency_id][-1], price_data[currency_id][0]) for currency_id in CURRENCY_IDS if currency_id != 'bitcoin']
            
            other_price_non_decrease = sum(1 for change in other_price_changes if change >= 0)
            other_price_non_increase = sum(1 for change in other_price_changes if change <= 0)
            
            if bitcoin_price_change < 0 and other_price_non_decrease / len(other_price_changes) >= 0.8:
                message = "Bitcoin's price dropped while at least 80% of other cryptocurrencies' prices did not drop."
                send_telegram_message(message)
            elif bitcoin_price_change > 0 and other_price_non_increase / len(other_price_changes) >= 0.8:
                message = "Bitcoin's price rose while at least 80% of other cryptocurrencies' prices did not rise."
                send_telegram_message(message)
        
        # Check volume changes for all cryptocurrencies
        for currency_id in CURRENCY_IDS:
            if len(volume_data[currency_id]) == 3:
                volume_change = calculate_change(volume_data[currency_id][-1], volume_data[currency_id][0])
                if abs(volume_change) >= 5:
                    direction = "increased" if volume_change > 0 else "decreased"
                    message = f"{currency_id.capitalize()}'s trading volume {direction} by at least 5%."
                    send_telegram_message(message)
        
        # Sleep until the next 5-minute mark
        time_to_sleep = 300 - (time.time() - start_time)
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)

if __name__ == '__main__':
    main()
