import ccxt
import requests
import time
from datetime import datetime, timedelta
from collections import deque

# Telegram Bot 配置
BOT_TOKEN = '5925179620:AAELdC5OfDHXqvpBNEx5xEOjCzcPdY0isck'
CHAT_ID = '1640026631'
TG_API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

# 初始化交易所
exchange = ccxt.binance()  # 你可以根据需要替换成其他交易所

# 用于存储历史数据的 deque（包含最近两天的数据）
historical_supplies = deque(maxlen=2)
historical_volumes = deque(maxlen=2)

def fetch_top_gainers():
    tickers = exchange.fetch_tickers()
    gainers = []

    for symbol, ticker in tickers.items():
        if not symbol.endswith('/USDT'):
            continue

        try:
            price = ticker['last']
            change_percent = ticker['percentage']
            if change_percent > 0:
                gainers.append({
                    'symbol': symbol,
                    'price': price,
                    'change_percent': change_percent,
                    'volume': ticker['quoteVolume']
                })
        except Exception as e:
            print(f'Error fetching data for {symbol}: {e}')

    # 排序并选择前五名涨幅最高的
    gainers = sorted(gainers, key=lambda x: x['change_percent'], reverse=True)[:5]
    return gainers

def fetch_current_supply_from_coingecko(symbol):
    url = f'https://api.coingecko.com/api/v3/coins/{symbol}'
    response = requests.get(url)
    data = response.json()
    return data['market_data']['circulating_supply']

def fetch_historical_volume(symbol):
    # 获取历史成交量
    since = exchange.parse8601((datetime.now() - timedelta(days=1)).isoformat())
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d', since=since)
    if ohlcv:
        return ohlcv[0][5]  # 'quoteVolume' is typically the 6th element
    return None

def update_historical_data(symbol):
    current_supply = fetch_current_supply_from_coingecko(symbol)
    historical_supply = historical_supplies[0] if len(historical_supplies) == 2 else None

    current_volume = fetch_historical_volume(symbol)
    historical_volume = historical_volumes[0] if len(historical_volumes) == 2 else None

    if len(historical_supplies) == 2 and len(historical_volumes) == 2:
        return (current_supply, historical_supply, current_volume, historical_volume)
    else:
        historical_supplies.append(current_supply)
        historical_volumes.append(current_volume)
        return (None, None, None, None)

def calculate_supply_growth_rate(current_supply, historical_supply):
    if historical_supply == 0:
        return float('inf')  # 避免除以零
    return (current_supply - historical_supply) / historical_supply

def calculate_volume_ratio(current_volume, historical_volume):
    if historical_volume == 0:
        return float('inf')  # 避免除以零
    return current_volume / historical_volume

def filter_and_notify(gainers):
    filtered = []

    for item in gainers:
        current_supply, historical_supply, current_volume, historical_volume = update_historical_data(item['symbol'])

        if (current_supply is not None and historical_supply is not None and 
            current_volume is not None and historical_volume is not None):
            growth_rate = calculate_supply_growth_rate(current_supply, historical_supply)
            volume_ratio = calculate_volume_ratio(current_volume, historical_volume)
            
            # 流通量的增量率低于价格涨幅
            # 成交量的增长率大于价格增长率的两倍
            if (item['price'] < 20 and
                item['change_percent'] > 10 and
                volume_ratio > 2 and  # 示例阈值：成交量相对显著增加的条件
                (volume_ratio - 1) > 2 * (item['change_percent'] / 100)  # 成交量增长率大于价格增长率的两倍
               ):
                filtered.append({
                    'symbol': item['symbol'],
                    'price': item['price'],
                    'change_percent': item['change_percent'],
                    'volume': item['volume'],
                    'current_supply': current_supply,
                    'historical_supply': historical_supply,
                    'growth_rate': growth_rate,
                    'volume_ratio': volume_ratio
                })

    if filtered:
        message = "符合条件的币种信息:\n"
        for item in filtered:
            message += (f"币种: {item['symbol']}\n"
                        f"价格: ${item['price']:.2f}\n"
                        f"涨幅: {item['change_percent']:.2f}%\n"
                        f"当前成交量: {item['volume']:.2f}\n"
                        f"当前流通量: {item['current_supply']:.2f}\n"
                        f"前一天流通量: {item['historical_supply']:.2f}\n"
                        f"流通量增长率: {item['growth_rate']:.2f}\n"
                        f"成交量流通量比: {item['volume_ratio']:.2f}\n\n")
        send_telegram_message(message)

def send_telegram_message(message):
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    response = requests.post(TG_API_URL, data=payload)
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")

def main():
    while True:
        gainers = fetch_top_gainers()
        filter_and_notify(gainers)
        time.sleep(300)  # 5 分钟的延迟

if __name__ == "__main__":
    main()
