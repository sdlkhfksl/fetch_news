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
PERCENT_CHANGE_BOT_TOKEN = '7087052045:AAF5Xh6hLIEndRY9YzjsmMuCJwJwTsMFa8M'  # Replace with your actual bot token for percent change alerts
PERCENT_CHANGE_CHAT_ID = '1640026631'  # Replace with your actual chat ID for percent change alerts

# TAAPI secret for ATR requests
TAAPI_SECRET = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbHVlIjoiNjVjZjI1ZTAyY2I5MTQwYWM1NjMxNzA2IiwiaWF0IjoxNzIyMzIxMTM0LCJleHAiOjMzMjI2Nzg1MTM0fQ.1h9soIXPH1l-IytxN-iFr89eiVBxbMRJsIP-5VBSIbw'  # Replace with your actual TAAPI secret

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

# Function to get ATR value from TAAPI
def get_atr(symbol, interval, secret):
    url = f'https://api.taapi.io/atr?secret={secret}&exchange=binance&symbol={symbol}&interval={interval}'
    response = requests.get(url)
    data = response.json()
    return data['value']

# Function to calculate stop loss and take profit levels
def calculate_stop_loss_take_profit(current_price, atr_value, multiplier=1.5):
    stop_loss = current_price - (atr_value * multiplier)
    take_profit = current_price + (atr_value * multiplier)
    return stop_loss, take_profit

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
            
            # Price breakout detection for BTC and ETH only
            if currency_id in ['BTCUSDT', 'ETHUSDT'] and len(price_data[currency_id]) >= 2:
                prev_price = price_data[currency_id][-2]
                current_price = price_data[currency_id][-1]
                threshold = 500 if currency_id == 'BTCUSDT' else 300
                current_level = int(current_price // threshold) * threshold
                prev_level = int(prev_price // threshold) * threshold

                if prev_level != current_level:
                    if current_price > prev_level:
                        message = f"{currency_id.upper()} price broke through ${current_level}. Current price: ${current_price}."
                    else:
                        message = f"{currency_id.upper()} price dropped below ${current_level}. Current price: ${current_price}."

                    # Fetch ATR and calculate stop loss/take profit only if there's a breakout
                    atr_value = get_atr(currency_id, '1h', TAAPI_SECRET)
                    stop_loss, take_profit = calculate_stop_loss_take_profit(current_price, atr_value)
                    message += f" ATR Value: {atr_value:.2f}. Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}."
                    
                    send_telegram_message(message)
    
    # Send regular alert messages
    if messages:
        send_telegram_message("\n".join(messages))
    
    # Send percent change alert messages
    if percent_change_messages:
        send_percent_change_message("\n".join(percent_change_messages))

# Function to safely make requests with retries
def safe_request(url, method='GET', **kwargs):
    for _ in range(3):
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logging.error(f"Request error: {e}")
            time.sleep(5)
    return None

# Main loop to check prices and notify every 60 seconds
if __name__ == "__main__":
    while True:
        check_prices_and_notify()
        time.sleep(60)
