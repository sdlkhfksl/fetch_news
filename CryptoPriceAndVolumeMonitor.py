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
    response = requests.get(url)
    data = response.json()[currency_id]
    return data['usd'], data['usd_24h_vol']

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    requests.post(url, data=payload)

def calculate_change(current, previous):
    return (current - previous) / previous * 100 if previous != 0 else 0

def main():
    price_data = {currency_id: deque(maxlen=3) for currency_id in CURRENCY_IDS}
    volume_data = {currency_id: deque(maxlen=3) for currency_id in CURRENCY_IDS}
    
    while True:
        for _ in range(25):  # 5 minutes / 12 seconds = 25 iterations
            for currency_id in CURRENCY_IDS:
                price, volume = get_price_and_volume(currency_id)
                price_data[currency_id].append(price)
                volume_data[currency_id].append(volume)
            
            time.sleep(12)  # Wait for 12 seconds before fetching new data
        
        if len(price_data['bitcoin']) == 3:
            bitcoin_price_change = calculate_change(price_data['bitcoin'][-1], price_data['bitcoin'][0])
            
            other_price_changes = [(calculate_change(price_data[currency_id][-1], price_data[currency_id][0])) for currency_id in CURRENCY_IDS if currency_id != 'bitcoin']
            
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

if __name__ == '__main__':
    main()
