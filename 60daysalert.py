import requests
import time
import logging
from collections import deque
from datetime import datetime, timezone

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# API Keys and Telegram Bot configuration
BOT_TOKEN = '7087052045:AAF3eJLHSvBGKtqqa2l_e7su_ESiteL8ai8'
CHAT_ID = '1640026631'
MESSARI_API_KEY = 'WsXyGZ85UQETYVfXhxLYhi01nV9CP1W0V34iO05Nfj76z1t9'
COINMARKETCAP_API_KEY = '8dcc830a-c866-405c-8531-357278d4f821'

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

# CoinMarketCap ID mapping
COINMARKETCAP_IDS = {
    'bitcoin': '1',
    'ethereum': '1027',
    'uniswap': '7083',
    'shiba-inu': '5994',
    'ripple': '52',
    'binancecoin': '1839',
    'cardano': '2010',
    'worldcoin': '13502',
    'solana': '5426',
    'avalanche-2': '5805',
    'polkadot': '6636',
    'the-open-network': '11419',
    'doge': '74'
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
    try:
        response = requests.get(url, headers={'x-messari-api-key': MESSARI_API_KEY})
        response.raise_for_status()
        price_data = response.json()
        return price_data['data']['market_data']['price_usd']
    except requests.RequestException as e:
        logging.error(f"Error fetching data from Messari for {currency_id}: {e}")
        return None

# 获取CoinMarketCap价格数据
def get_price_from_coinmarketcap(currency_id):
    cmc_id = COINMARKETCAP_IDS[currency_id]
    url = f'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
    params = {
        'id': cmc_id
    }
    headers = {
        'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
        'Accept': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        price_data = response.json()
        return price_data['data'][str(cmc_id)]['quote']['USD']['price']
    except requests.RequestException as e:
        logging.error(f"Error fetching data from CoinMarketCap for {currency_id}: {e}")
        return None

# 发送Telegram消息
def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        logging.info(f"Message sent successfully: {message}")
    except requests.RequestException as e:
        logging.error(f"Failed to send message: {message}")
        logging.exception(e)

# 更新并检查价格
def update_and_check_price(currency_id, price):
    today = datetime.now(timezone.utc).date()
    logging.debug(f"Updating and checking price for {currency_id} at ${price}")

    if not prices[currency_id] or prices[currency_id][-1][0] != today:
        if len(prices[currency_id]) == MAX_DAYS:
            logging.info(f"Removing oldest price for {currency_id}: {prices[currency_id].popleft()}")
        prices[currency_id].append((today, price))
        logging.info(f"Added new price for {currency_id}: {price}")

    messages = []
    lowest_day, highest_day = None, None

    for days in reversed(time_ranges):
        relevant_prices = list(prices[currency_id])[-days:]

        # 检查最低价格
        lowest_today = min(relevant_prices, key=lambda x: x[1], default=(today, float('inf')))
        if price < lowest_today[1]:
            lowest_day = days

        # 检查最高价格
        highest_today = max(relevant_prices, key=lambda x: x[1], default=(today, float('-inf')))
        if price > highest_today[1]:
            highest_day = days

    if lowest_day:
        messages.append(f"{currency_id.upper()} new low price alert in {lowest_day}-day range! Current price: ${price}")

    if highest_day:
        messages.append(f"{currency_id.upper()} new high price alert in {highest_day}-day range! Current price: ${price}")

    if messages:
        message = "\n".join(messages)
        logging.info(f"Combined message for {currency_id}: {message}")
        send_telegram_message(message)

# 主逻辑
def main():
    global use_messari
    while True:
        start_time = datetime.now(timezone.utc)
        try:
            for currency_id in CURRENCY_IDS:
                logging.info(f"Fetching price for {currency_id}")
                if use_messari:
                    price = get_price_from_messari(currency_id)
                else:
                    price = get_price_from_coinmarketcap(currency_id)
                
                if price is not None:
                    logging.info(f"Fetched price for {currency_id}: ${price}")
                    update_and_check_price(currency_id, price)
                else:
                    logging.error(f"Failed to fetch price for {currency_id}")

                time.sleep(5)  # 每次请求后等待5秒

        except Exception as e:
            logging.exception("An error occurred during the main loop.")

        # 切换 API
        use_messari = not use_messari

        # 等待至下一循环的开始
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logging.info(f"Loop completed in {elapsed:.2f} seconds, waiting for next cycle.")
        time.sleep(max(0, 120 - elapsed))  # 等待2分钟

if __name__ == "__main__":
    main()
