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
lowest_prices = {currency: deque(maxlen=MAX_DAYS) for currency in CURRENCY_IDS}
highest_prices = {currency: deque(maxlen=MAX_DAYS) for currency in CURRENCY_IDS}

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

# 获取CoinMarketCap价格数据（批量请求）
def get_price_from_coinmarketcap():
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    ids = ','.join(map(str, COINMARKETCAP_IDS.values()))
    parameters = {
        'id': ids
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
    }
    try:
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status()
        price_data = response.json()
        return {currency: price_data['data'][str(COINMARKETCAP_IDS[currency])]['quote']['USD']['price']
                for currency in COINMARKETCAP_IDS}
    except requests.RequestException as e:
        logging.error(f"Error fetching data from CoinMarketCap: {e}")
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
    logging.info(f"Updating and checking price for {currency_id} at ${price}")

    # 更新最低价格
    if not lowest_prices[currency_id] or lowest_prices[currency_id][-1][0] != today:
        if len(lowest_prices[currency_id]) == MAX_DAYS:
            logging.info(f"Removing oldest low price for {currency_id}: {lowest_prices[currency_id].popleft()}")
        lowest_prices[currency_id].append((today, price))
        logging.info(f"Added new low price for {currency_id}: {price}")
    else:
        _, lowest_today = lowest_prices[currency_id][-1]
        if price < lowest_today:
            lowest_prices[currency_id][-1] = (today, price)
            logging.info(f"Updated today's low price for {currency_id} to {price}")
            # 检查是否为所有记录中的最低价格
            for time_range in sorted(time_ranges, reverse=True):
                if len(lowest_prices[currency_id]) >= time_range and all(price < day_price for _, day_price in list(lowest_prices[currency_id])[-time_range:]):
                    message = f"{currency_id.upper()} new {time_range}-day low price alert! Current price: ${price}"
                    logging.info(f"Sending low price alert for {currency_id}: {message}")
                    send_telegram_message(message)
                    break

    # 更新最高价格
    if not highest_prices[currency_id] or highest_prices[currency_id][-1][0] != today:
        if len(highest_prices[currency_id]) == MAX_DAYS:
            logging.info(f"Removing oldest high price for {currency_id}: {highest_prices[currency_id].popleft()}")
        highest_prices[currency_id].append((today, price))
        logging.info(f"Added new high price for {currency_id}: {price}")
    else:
        _, highest_today = highest_prices[currency_id][-1]
        if price > highest_today:
            highest_prices[currency_id][-1] = (today, price)
            logging.info(f"Updated today's high price for {currency_id} to {price}")
            # 检查是否为所有记录中的最高价格
            for time_range in sorted(time_ranges, reverse=True):
                if len(highest_prices[currency_id]) >= time_range and all(price > day_price for _, day_price in list(highest_prices[currency_id])[-time_range:]):
                    message = f"{currency_id.upper()} new {time_range}-day high price alert! Current price: ${price}"
                    logging.info(f"Sending high price alert for {currency_id}: {message}")
                    send_telegram_message(message)
                    break

# 主逻辑
def main():
    global use_messari
    while True:
        start_time = datetime.now(timezone.utc)
        try:
            if use_messari:
                for currency_id in CURRENCY_IDS:
                    logging.info(f"Fetching price for {currency_id} from Messari")
                    price = get_price_from_messari(currency_id)
                    if price is not None:
                        logging.info(f"Fetched price for {currency_id} from Messari: ${price}")
                        update_and_check_price(currency_id, price)
                    else:
                        logging.error(f"Failed to fetch price for {currency_id} from Messari")
                    time.sleep(5)  # 每次请求后等待5秒
            else:
                logging.info("Fetching prices for all currencies from CoinMarketCap")
                prices_data = get_price_from_coinmarketcap()
                if prices_data:
                    for currency_id, price in prices_data.items():
                        logging.info(f"Fetched price for {currency_id} from CoinMarketCap: ${price}")
                        update_and_check_price(currency_id, price)
                else:
                    logging.error("Failed to fetch prices from CoinMarketCap")
                
            # 切换 API
            use_messari = not use_messari
            
            # 等待2分钟
            time_elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            sleep_time = max(0, 120 - time_elapsed)
            time.sleep(sleep_time)
            
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            time.sleep(60)  # 错误发生时等待60秒

if __name__ == "__main__":
    main()
