import requests
import time
import logging
from collections import deque
from datetime import datetime, timezone

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Keys and Telegram Bot configuration
BOT_TOKEN = '7087052045:AAF3eJLHSvBGKtqqa2l_e7su_ESiteL8ai8'
CHAT_ID = '1640026631'
MESSARI_API_KEY = 'WsXyGZ85UQETYVfXhxLYhi01nV9CP1W0V34iO05Nfj76z1t9'
COINCAP_API_KEY = '984de562-4fb3-43a2-8fcd-1d1af4b39789'

# Currency IDs
CURRENCY_IDS = {
    'bitcoin': '1e31218a-e44e-4285-820c-8282ee222035',
    'ethereum': '21c795f5-1bfd-40c3-858e-e9d7e820c6d0',
    'uniswap': '1d51479d-68f6-4886-8644-2a55ea9007bf',
    'shiba-inu': '8c4f84a7-6484-4074-8c17-fe363a243e7f',
    'ripple': '97775be0-2608-4720-b7af-f85b24c7eb2d',
    'binancecoin': '7dc551ba-cfed-4437-a027-386044415e3e',
    'cardano': '362f0140-ecdd-4205-b8a0-36f0fd5d8167',
    'worldcoin': 'd22cb290-a80a-4ee4-be8e-ea81e6e1b706',
    'solana': 'b3d5d66c-26a2-404c-9325-91dc714a722b',
    'avalanche-2': '2db6b38a-681a-4514-9d67-691e319597ee',
    'polkadot': 'da6a0575-ec95-4c47-855d-5fc6a3e22ada',
    'the-open-network': '2023433a-23f4-4901-822d-a537b0c71676',
    'doge': '7d793fa7-5fc6-432a-b26b-d1b10769d42e'
}

# CoinCap ID mapping
COINCAP_IDS = {
    'bitcoin': 'bitcoin',
    'ethereum': 'ethereum',
    'uniswap': 'uniswap',
    'shiba-inu': 'shiba-inu',
    'ripple': 'xrp',
    'binancecoin': 'binance-coin',
    'cardano': 'cardano',
    'worldcoin': 'worldcoin',
    'solana': 'solana',
    'avalanche-2': 'avalanche',
    'polkadot': 'polkadot',
    'the-open-network': 'toncoin',
    'doge': 'dogecoin'
}

# Deque对象用于保存每天的最低价格和最高价格
MAX_DAYS = 60
time_ranges = [7, 15, 30, 60]
prices = {currency: deque(maxlen=MAX_DAYS) for currency in CURRENCY_IDS}

# API切换标志
use_messari = True

# 获取Messari价格数据
def get_price_from_messari(currency_id):
    messari_id = CURRENCY_IDS[currency_id]
    url = f'https://data.messari.io/api/v1/assets/{messari_id}/metrics/market-data'
    response = requests.get(url, headers={'x-messari-api-key': MESSARI_API_KEY})
    response.raise_for_status()
    price_data = response.json()
    return price_data['data']['market_data']['price_usd']

# 获取CoinCap价格数据
def get_price_from_coincap(currency_id):
    cap_id = COINCAP_IDS[currency_id]
    url = f'https://api.coincap.io/v2/assets/{cap_id}'
    response = requests.get(url, headers={'Authorization': f'Bearer {COINCAP_API_KEY}'})
    response.raise_for_status()
    price_data = response.json()
    return float(price_data['data']['priceUsd'])

# 发送Telegram消息
def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': CHAT_ID,
        'text': message
    }
    response = requests.post(url, json=data)
    response.raise_for_status()

# 更新并检查价格
def update_and_check_price(currency_id, price):
    today = datetime.now(timezone.utc).date()
    logging.info(f"Updating and checking price for {currency_id} at ${price}")

    if not prices[currency_id] or prices[currency_id][-1][0] != today:
        if len(prices[currency_id]) == MAX_DAYS:
            logging.info(f"Removing oldest price for {currency_id}: {prices[currency_id].popleft()}")
        prices[currency_id].append((today, price))
        logging.info(f"Added new price for {currency_id}: {price}")

    for days in time_ranges:
        relevant_prices = list(prices[currency_id])[-days:]

        # 检查最低价格
        lowest_today = min(relevant_prices, key=lambda x: x[1])
        if price < lowest_today[1]:
            message = f"{currency_id.upper()} new low price alert in {days}-day range! Current price: ${price}"
            logging.info(f"Sending low price alert for {currency_id} in {days}-day range: {message}")
            send_telegram_message(message)

        # 检查最高价格
        highest_today = max(relevant_prices, key=lambda x: x[1])
        if price > highest_today[1]:
            message = f"{currency_id.upper()} new high price alert in {days}-day range! Current price: ${price}"
            logging.info(f"Sending high price alert for {currency_id} in {days}-day range: {message}")
            send_telegram_message(message)

# 主逻辑
def main():
    global use_messari
    while True:
        start_time = datetime.now(timezone.utc)
        try:
            for currency_id in CURRENCY_IDS:
                if use_messari:
                    price = get_price_from_messari(currency_id)
                else:
                    price = get_price_from_coincap(currency_id)
                logging.info(f"Fetched price for {currency_id}: ${price}")
                update_and_check_price(currency_id, price)
                time.sleep(5)  # 每次请求后等待5秒
        except requests.RequestException as e:
            logging.exception("Network error occurred while fetching and updating prices.")
        except Exception as e:
            logging.exception("An error occurred while fetching and updating prices.")
        # 切换 API
        use_messari = not use_messari
        # 等待至下一分钟的开始
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logging.info(f"Loop completed in {elapsed:.2f} seconds, waiting for next cycle.")
        time.sleep(max(0, 60 - elapsed))

if __name__ == "__main__":
    main()
