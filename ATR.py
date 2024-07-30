import requests
import time
import logging
from collections import deque

# Constants
TAAPI_SECRET = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbHVlIjoiNjVjZjI1ZTAyY2I5MTQwYWM1NjMxNzA2IiwiaWF0IjoxNzIyMzIxMTM0LCJleHAiOjMzMjI2Nzg1MTM0fQ.1h9soIXPH1l-IytxN-iFr89eiVBxbMRJsIP-5VBSIbw'  # Your actual TAAPI secret
BOT_TOKEN = '7087052045:AAF3eJLHSvBGKtqqa2l_e7su_ESiteL8ai8'
CHAT_ID = '1640026631'

# Deques to store recent prices
price_data = {
    'bitcoin': deque(maxlen=2),
    'ethereum': deque(maxlen=2)
}

def get_price(symbol):
    url = f'https://api.taapi.io/price?secret={TAAPI_SECRET}&exchange=binance&symbol={symbol}&interval=1m'
    response = requests.get(url)
    data = response.json()
    return data['close']

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=payload)

def get_atr(symbol, interval, secret):
    url = f'https://api.taapi.io/atr?secret={secret}&exchange=binance&symbol={symbol}&interval={interval}'
    response = requests.get(url)
    data = response.json()
    return data['value']

def calculate_stop_loss_take_profit(current_price, atr_value, multiplier=1.5):
    stop_loss = current_price - (atr_value * multiplier)
    take_profit = current_price + (atr_value * multiplier)
    return stop_loss, take_profit

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

while True:
    try:
        # Fetch Bitcoin price
        btc_price = get_price('BTC/USDT')
        time.sleep(15)

        # Fetch Ethereum price
        eth_price = get_price('ETH/USDT')
        time.sleep(15)

        # Update price data
        price_data['bitcoin'].append(btc_price)
        price_data['ethereum'].append(eth_price)

        logging.info(f'Bitcoin Price: {btc_price}, Ethereum Price: {eth_price}')

        # Check Bitcoin price changes
        if len(price_data['bitcoin']) == 2:
            bitcoin_current_price = price_data['bitcoin'][-1]
            bitcoin_prev_price = price_data['bitcoin'][0]
            bitcoin_current_level = int(bitcoin_current_price // 500) * 500
            bitcoin_prev_level = int(bitcoin_prev_price // 500) * 500

            logging.info(f'Bitcoin Current Level: {bitcoin_current_level}, Bitcoin Previous Level: {bitcoin_prev_level}')

            if bitcoin_prev_level < bitcoin_current_level:
                message = f"Bitcoin's price broke through ${bitcoin_current_level}. Current price: ${bitcoin_current_price}."
                send_telegram_message(message)
                logging.info(message)
                atr_value = get_atr('BTC/USDT', '1h', TAAPI_SECRET)
                time.sleep(15)
                stop_loss, take_profit = calculate_stop_loss_take_profit(bitcoin_current_price, atr_value)
                atr_message = f"ATR Value: {atr_value}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}"
                send_telegram_message(atr_message)
                logging.info(atr_message)
                time.sleep(15)
            elif bitcoin_prev_level > bitcoin_current_level:
                message = f"Bitcoin's price dropped below ${bitcoin_current_level}. Current price: ${bitcoin_current_price}."
                send_telegram_message(message)
                logging.info(message)
                atr_value = get_atr('BTC/USDT', '1h', TAAPI_SECRET)
                time.sleep(15)
                stop_loss, take_profit = calculate_stop_loss_take_profit(bitcoin_current_price, atr_value)
                atr_message = f"ATR Value: {atr_value}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}"
                send_telegram_message(atr_message)
                logging.info(atr_message)
                time.sleep(15)

        # Check Ethereum price changes
        if len(price_data['ethereum']) == 2:
            ethereum_current_price = price_data['ethereum'][-1]
            ethereum_prev_price = price_data['ethereum'][0]
            ethereum_current_level = int(ethereum_current_price // 300) * 300
            ethereum_prev_level = int(ethereum_prev_price // 300) * 300

            logging.info(f'Ethereum Current Level: {ethereum_current_level}, Ethereum Previous Level: {ethereum_prev_level}')

            if ethereum_prev_level < ethereum_current_level:
                message = f"Ethereum's price broke through ${ethereum_current_level}. Current price: ${ethereum_current_price}."
                send_telegram_message(message)
                logging.info(message)
                atr_value = get_atr('ETH/USDT', '1h', TAAPI_SECRET)
                time.sleep(15)
                stop_loss, take_profit = calculate_stop_loss_take_profit(ethereum_current_price, atr_value)
                atr_message = f"ATR Value: {atr_value}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}"
                send_telegram_message(atr_message)
                logging.info(atr_message)
                time.sleep(15)
            elif ethereum_prev_level > ethereum_current_level:
                message = f"Ethereum's price dropped below ${ethereum_current_level}. Current price: ${ethereum_current_price}."
                send_telegram_message(message)
                logging.info(message)
                atr_value = get_atr('ETH/USDT', '1h', TAAPI_SECRET)
                time.sleep(15)
                stop_loss, take_profit = calculate_stop_loss_take_profit(ethereum_current_price, atr_value)
                atr_message = f"ATR Value: {atr_value}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}"
                send_telegram_message(atr_message)
                logging.info(atr_message)
                time.sleep(15)

    except Exception as e:
        logging.error(f"Error: {e}")

    time.sleep(60)  # Ensures at least 60 seconds between each loop iteration
