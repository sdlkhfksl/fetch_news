import logging
import time
from binance.client import Client
from collections import deque
import requests

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# The Telegram bot token and chat ID for general alerts
TELEGRAM_TOKEN = '6205901139:AAE1fttg5w8FTjKKhZSlgUljwU9klFGxkZw'  # Replace with your actual bot token for general alerts
TELEGRAM_CHAT_ID = '1640026631'  # Replace with your actual chat ID for general alerts

# Additional Telegram bot token and chat ID for percent change notifications
PERCENT_CHANGE_BOT_TOKEN = '7087052045:AAF3eJLHSvBGKtqqa2l_e7su_ESiteL8ai8'  # Replace with your actual bot token for percent change alerts
PERCENT_CHANGE_CHAT_ID = '1640026631'  # Replace with your actual chat ID for percent change alerts

# List of cryptocurrencies to monitor (symbol format for Binance)
CURRENCY_IDS = [
    'BTCUSDT',
    'DOGEUSDT',
    'ETHUSDT',
    'UNIUSDT',
    'SHIBUSDT',
    'XRPUSDT',
    'BNBUSDT',
    'ADAUSDT',
    'WLDUSDT',
    'SOLUSDT',
    'AVAXUSDT',
    'DOTUSDT',
    'TONUSDT',
    # ... other currencies ...
]

# Price thresholds and percent change configuration for alerts
PRICE_ALERTS = {
    'BTCUSDT': {'low': 39000, 'high': 50000, 'percent_change': 5},
    'DOGEUSDT': {'low': 0.07, 'high': 0.1, 'percent_change': 5},
    'ETHUSDT': {'low': 1700, 'high': 2500, 'percent_change': 5},
    'UNIUSDT': {'low': 4.2, 'high': 6, 'percent_change': 5},
    'SHIBUSDT': {'low': 0.0000085, 'high': 0.00001, 'percent_change': 5},
    'XRPUSDT': {'low': 0.3, 'high': 0.5, 'percent_change': 5},
    'BNBUSDT': {'low': 210, 'high': 300, 'percent_change': 5},
    'ADAUSDT': {'low': 0.42, 'high': 0.6, 'percent_change': 5},
    'WLDUSDT': {'low': 1.9, 'high': 3, 'percent_change': 5},
    'SOLUSDT': {'low': 24, 'high': 111, 'percent_change': 5},
    'AVAXUSDT': {'low': 10, 'high': 40, 'percent_change': 5},
    'DOTUSDT': {'low': 4, 'high': 7.7, 'percent_change': 5},
    'TONUSDT': {'low': 5, 'high': 6.5, 'percent_change': 5},
    # ... other currency thresholds...
}

# Binance API setup
API_KEY = 'ZDiQca9mtsOS7f9wzn8tW59lqB2z9bqv0O9upbcXcA6O2InXBFpAvGmkiq4QrFxA'  # Your Binance API Key
API_SECRET = 'XGm2ckG307TosvwTpfB7ARs4xlL2ynVzKgkR5vZ3WYcS2r1IIDZRKUg6jixpVIGc'  # Your Binance API Secret

client = Client(API_KEY, API_SECRET)
price_data = {currency: deque(maxlen=10) for currency in CURRENCY_IDS}

# Function to fetch current prices from Binance
def get_crypto_prices_binance(symbols):
    prices = {}
    for symbol in symbols:
        try:
            ticker = client.get_symbol_ticker(symbol=symbol)
            prices[symbol] = float(ticker['price'])
        except Exception as e:
            logging.error(f"Error fetching spot price for {symbol}: {e}")
            try:
                futures_ticker = client.futures_symbol_ticker(symbol=symbol)
                prices[symbol] = float(futures_ticker['price'])
            except Exception as fe:
                logging.error(f"Error fetching futures price for {symbol}: {fe}")
    return prices

# Function to send a message via Telegram for general alerts
def send_telegram_message(message):
    safe_request(
        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
        method='POST',
        json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
    )

# Function to send a percent change message via Telegram for specific alerts
def send_percent_change_message(message):
    safe_request(
        f'https://api.telegram.org/bot{PERCENT_CHANGE_BOT_TOKEN}/sendMessage',
        method='POST',
        json={
            'chat_id': PERCENT_CHANGE_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
    )

# Function to calculate percent changes and check thresholds
def calculate_percent_changes(prices, currency_id):
    percent_changes = []
    for i in range(1, len(prices)):
        percent_change = 100.0 * (prices[-1] - prices[-i-1]) / prices[-i-1]
        if abs(percent_change) >= PRICE_ALERTS[currency_id]['percent_change']:
            percent_changes.append(f"{currency_id.upper()} price changed by {percent_change:.2f}% in the last {i} minute(s)")
    return percent_changes

# Function to check prices and notify
def check_prices_and_notify():
    messages = []
    percent_change_messages = []
    current_prices = get_crypto_prices_binance(CURRENCY_IDS)
    for currency_id in CURRENCY_IDS:
        price_info = current_prices.get(currency_id)
        if price_info:
            price_data[currency_id].append(price_info)
            low_price = PRICE_ALERTS[currency_id]['low']
            high_price = PRICE_ALERTS[currency_id]['high']
            if price_info <= low_price:
                messages.append(f"{currency_id.upper()} price drop alert: ${price_info}")
            elif price_info >= high_price:
                messages.append(f"{currency_id.upper()} price rise alert: ${price_info}")
            
            if len(price_data[currency_id]) >= 2:
                percent_change_messages.extend(calculate_percent_changes(price_data[currency_id], currency_id))
    
    # Send regular alert messages
    if messages:
        send_telegram_message("\n".join(messages))
    
    # Send percent change alert messages to the specific bot
    for message in percent_change_messages:
        send_percent_change_message(message)

# Safe request function to handle network errors and rate limiting
def safe_request(url, method='GET', params=None, json=None, headers=None):
    while True:
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers)
            else:
                response = requests.post(url, json=json, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            if response and response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 120))
                logging.warning(f"Rate limit hit. Retrying in {retry_after} seconds.")
                time.sleep(retry_after)
            else:
                logging.error(f"HTTP error occurred: {http_err}")
                time.sleep(10)
        except requests.exceptions.ConnectionError as conn_err:
            logging.error(f"Connection error occurred: {conn_err}")
            time.sleep(10)
        except requests.exceptions.Timeout as timeout_err:
            logging.error(f"Timeout error occurred: {timeout_err}")
            time.sleep(10)
        except Exception as err:
            logging.error(f"An unexpected error occurred: {err}")
            time.sleep(10)

# Main script function
def main():
    try:
        while True:
            check_prices_and_notify()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logging.info("Script execution interrupted by user")
    except Exception as e:
        logging.exception(f"An error occurred: {e}")
        time.sleep(60)  # Wait a minute and try again

# Run the main function when the script is executed
if __name__ == '__main__':
    main()
