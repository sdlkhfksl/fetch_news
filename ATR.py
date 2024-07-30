import requests
import time
import logging
from collections import deque

# Constants
TAAPI_SECRET = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbHVlIjoiNjVjZjI1ZTAyY2I5MTQwYWM1NjMxNzA2IiwiaWF0IjoxNzIyMzIxMTM0LCJleHAiOjMzMjI2Nzg1MTM0fQ.1h9soIXPH1l-IytxN-iFr89eiVBxbMRJsIP-5VBSIbw'
BOT_TOKEN = '7087052045:AAF3eJLHSvBGKtqqa2l_e7su_ESiteL8ai8'
CHAT_ID = '1640026631'

# Global variables to store last checked levels
last_checked_btc_level = None
last_checked_eth_level = None

# Deques to store recent prices
price_data = {
    'bitcoin': deque(maxlen=2),
    'ethereum': deque(maxlen=2)
}

# Setup logging
logging.basicConfig(filename='crypto_monitor.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def get_price(symbol):
    try:
        url = f'https://api.taapi.io/price?secret={TAAPI_SECRET}&exchange=binance&symbol={symbol}&interval=1m'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['close']
    except Exception as e:
        logging.error(f"Error fetching price for {symbol}: {e}")
        return None

def send_telegram_message(message):
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        payload = {'chat_id': CHAT_ID, 'text': message}
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")

def get_atr(symbol, interval, secret):
    try:
        url = f'https://api.taapi.io/atr?secret={secret}&exchange=binance&symbol={symbol}&interval={interval}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['value']
    except Exception as e:
        logging.error(f"Error fetching ATR for {symbol}: {e}")
        return None

def calculate_stop_loss_take_profit(current_price, atr_value, multiplier=1.5):
    stop_loss = current_price - (atr_value * multiplier)
    take_profit = current_price + (atr_value * multiplier)
    return stop_loss, take_profit

while True:
    try:
        start_time = time.time()

        # Fetch Bitcoin price
        btc_price = get_price('BTC/USDT')
        if btc_price:
            price_data['bitcoin'].append(btc_price)
        time.sleep(15)

        # Fetch Ethereum price
        eth_price = get_price('ETH/USDT')
        if eth_price:
            price_data['ethereum'].append(eth_price)
        time.sleep(15)

        # Check Bitcoin price changes
        if len(price_data['bitcoin']) == 2:
            bitcoin_current_price = price_data['bitcoin'][-1]
            bitcoin_prev_price = price_data['bitcoin'][0]
            bitcoin_current_level = int(bitcoin_current_price // 500) * 500

            if last_checked_btc_level is None:
                last_checked_btc_level = int(bitcoin_prev_price // 500) * 500

            if bitcoin_prev_price < bitcoin_current_level and bitcoin_current_price >= bitcoin_current_level:
                message = f"Bitcoin's price broke through ${bitcoin_current_level}. Current price: ${bitcoin_current_price}."
                send_telegram_message(message)
                time.sleep(15)
                atr_value = get_atr('BTC/USDT', '1h', TAAPI_SECRET)
                if atr_value:
                    stop_loss, take_profit = calculate_stop_loss_take_profit(bitcoin_current_price, atr_value)
                    atr_message = f"ATR Value: {atr_value}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}"
                    send_telegram_message(atr_message)
                time.sleep(15)
            elif bitcoin_prev_price > bitcoin_current_level and bitcoin_current_price <= bitcoin_current_level:
                message = f"Bitcoin's price dropped below ${bitcoin_current_level}. Current price: ${bitcoin_current_price}."
                send_telegram_message(message)
                time.sleep(15)
                atr_value = get_atr('BTC/USDT', '1h', TAAPI_SECRET)
                if atr_value:
                    stop_loss, take_profit = calculate_stop_loss_take_profit(bitcoin_current_price, atr_value)
                    atr_message = f"ATR Value: {atr_value}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}"
                    send_telegram_message(atr_message)
                time.sleep(15)
            last_checked_btc_level = bitcoin_current_level

        # Check Ethereum price changes
        if len(price_data['ethereum']) == 2:
            ethereum_current_price = price_data['ethereum'][-1]
            ethereum_prev_price = price_data['ethereum'][0]
            ethereum_current_level = int(ethereum_current_price // 300) * 300

            if last_checked_eth_level is None:
                last_checked_eth_level = int(ethereum_prev_price // 300) * 300

            if ethereum_prev_price < ethereum_current_level and ethereum_current_price >= ethereum_current_level:
                message = f"Ethereum's price broke through ${ethereum_current_level}. Current price: ${ethereum_current_price}."
                send_telegram_message(message)
                time.sleep(15)
                atr_value = get_atr('ETH/USDT', '1h', TAAPI_SECRET)
                if atr_value:
                    stop_loss, take_profit = calculate_stop_loss_take_profit(ethereum_current_price, atr_value)
                    atr_message = f"ATR Value: {atr_value}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}"
                    send_telegram_message(atr_message)
                time.sleep(15)
            elif ethereum_prev_price > ethereum_current_level and ethereum_current_price <= ethereum_current_level:
                message = f"Ethereum's price dropped below ${ethereum_current_level}. Current price: ${ethereum_current_price}."
                send_telegram_message(message)
                time.sleep(15)
                atr_value = get_atr('ETH/USDT', '1h', TAAPI_SECRET)
                if atr_value:
                    stop_loss, take_profit = calculate_stop_loss_take_profit(ethereum_current_price, atr_value)
                    atr_message = f"ATR Value: {atr_value}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}"
                    send_telegram_message(atr_message)
                time.sleep(15)
            last_checked_eth_level = ethereum_current_level

        # Ensure the loop runs with a minimum of 60 seconds
        elapsed_time = time.time() - start_time
        if elapsed_time < 60:
            time.sleep(60 - elapsed_time)

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        time.sleep(60)  # Wait before retrying in case of an error
