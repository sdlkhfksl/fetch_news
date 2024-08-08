import ccxt
import requests
import time
import numpy as np
import logging

# 配置日志记录
logging.basicConfig(filename='crypto_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 配置 Telegram Bot
TELEGRAM_API_URL = 'https://api.telegram.org/bot5925179620:AAELdC5OfDHXqvpBNEx5xEOjCzcPdY0isck/sendMessage'
CHAT_ID = '1640026631'

# 配置 ccxt
exchange = ccxt.binance()  # 使用 Binance 作为示例，你可以根据需要更改为其他交易所

# 存储历史交易量数据
history = {}

def send_telegram_message(message):
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(TELEGRAM_API_URL, data=payload)
        if response.status_code != 200:
            logging.error(f"Error sending message: {response.text}")
    except Exception as e:
        logging.error(f"Exception in sending message: {e}")

def get_market_data():
    data = []
    
    try:
        # 获取所有市场
        markets = exchange.load_markets()
        symbols = [symbol for symbol in markets if symbol.endswith('USDT')]
        
        # 批量获取数据
        for symbol in symbols:
            try:
                ticker = exchange.fetch_ticker(symbol)
                last_price = ticker['last']
                percent_change = ticker['percentage']
                volume = ticker['quoteVolume']
                market_cap = last_price * volume  # 简化的市值计算
                
                # 更新历史数据
                if symbol not in history:
                    history[symbol] = []
                history[symbol].append(volume)
                
                # 保持历史数据的长度限制
                if len(history[symbol]) > 30:  # 保留过去30天的数据
                    history[symbol].pop(0)
                
                # 初步过滤
                if 2 <= last_price <= 20 and abs(percent_change) >= 10:
                    avg_volume = np.mean(history[symbol])  # 计算历史平均交易量
                    data.append({
                        'symbol': symbol,
                        'price': last_price,
                        'percent_change': percent_change,
                        'volume': volume,
                        'market_cap': market_cap,
                        'avg_volume': avg_volume
                    })
            except Exception as e:
                logging.error(f"Error fetching data for {symbol}: {e}")
    
    except Exception as e:
        logging.error(f"Exception in get_market_data: {e}")
    
    return data

def filter_cryptos(data):
    filtered = []
    for crypto in data:
        if crypto['volume'] > 1.5 * crypto['avg_volume'] and crypto['market_cap'] <= 1_000_000_000:
            filtered.append(crypto)
    return filtered

def main():
    while True:
        try:
            market_data = get_market_data()
            filtered_data = filter_cryptos(market_data)
            
            for crypto in filtered_data:
                message = (f"币种: {crypto['symbol']}\n"
                           f"当前价格: ${crypto['price']:.2f}\n"
                           f"每日变动: {crypto['percent_change']:.2f}%\n"
                           f"交易量: {crypto['volume']:.2f} (历史平均: {crypto['avg_volume']:.2f})\n"
                           f"市值: ${crypto['market_cap']:.2f}")
                send_telegram_message(message)
        
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
        
        time.sleep(300)  # 每5分钟运行一次

if __name__ == "__main__":
    main()
