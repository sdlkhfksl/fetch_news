import time
import requests
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 配置
TAAPI_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbHVlIjoiNjVjZjIzYzUyY2I5MTQwYWM1NjJjYzczIiwiaWF0IjoxNzIwNTA3MTY0LCJleHAiOjMzMjI0OTcxMTY0fQ.DUOCdUnjc_HijD0vhBZXu9dtj9f1UFzTP6gBwpWR_9c'
TELEGRAM_BOT_TOKEN = '5959250165:AAF5Xh6hLIEndRY9YzjsmMuCJwJwTsMFa8M'
TELEGRAM_CHAT_ID = '1640026631'
YOUR_CRYPTOCOMPARE_API_KEY = 'f71cf8d61d8774c76d598ad982ff4f6860d9b15777c2fb4e3e4580d3087109b5'
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
INTERVAL = '1h'

# Logging 配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Requests Session
session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        logger.info(f"Telegram message sent successfully: {message}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")

def fetch_taapi_data(indicator, symbol):
    url = f"https://api.taapi.io/{indicator}"
    params = {
        'secret': TAAPI_API_KEY,
        'exchange': 'binance',
        'symbol': symbol,
        'interval': INTERVAL
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {indicator} data for {symbol}: {e}")
        return None

def fetch_current_price(symbol):
    symbol_map = {
        'BTC/USDT': 'bitcoin',
        'ETH/USDT': 'ethereum',
        'BNB/USDT': 'binancecoin'
    }
    coingecko_id = symbol_map.get(symbol)
    if not coingecko_id:
        raise ValueError(f"Symbol {symbol} is not supported")
    
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': coingecko_id,
        'vs_currencies': 'usd'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data[coingecko_id]['usd']
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch current price for {symbol}: {e}")
        return None

def get_market_data(symbol, limit=150):
    symbol_map = {
        'BTC/USDT': 'BTC',
        'ETH/USDT': 'ETH',
        'BNB/USDT': 'BNB'
    }
    currency_id = symbol_map.get(symbol)
    if not currency_id:
        raise ValueError(f"Symbol {symbol} is not supported")
    
    url = f"https://min-api.cryptocompare.com/data/v2/histohour"
    params = {
        'fsym': currency_id,
        'tsym': 'USD',
        'limit': limit,
        'api_key': YOUR_CRYPTOCOMPARE_API_KEY,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if 'Data' in data and 'Data' in data['Data']:
            return pd.DataFrame(data['Data']['Data'])[['time', 'close', 'volumefrom']]
        else:
            logger.error(f"Unexpected response format: {data}")
            return pd.DataFrame(columns=['time', 'close', 'volumefrom'])
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}")
        return pd.DataFrame(columns=['time', 'close', 'volumefrom'])

def calculate_macd_rsi(df):
    if df.empty:
        logger.warning("Dataframe is empty. Skipping indicator calculation.")
        return df
    df['fast_ema'] = df['close'].ewm(span=12, adjust=False).mean()
    df['slow_ema'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['fast_ema'] - df['slow_ema']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['rsi'] = 100 - (100 / (1 + df['close'].pct_change().rolling(window=14).apply(lambda x: (x[x > 0].sum() / abs(x[x <= 0].sum())), raw=True)))
    df['volume'] = df['volumefrom']
    return df

def analyze_market(data, current_price):
    bbands = data.get('bbands', {})
    dmi = data.get('dmi', {})
    roc = data.get('roc', {})
    psar = data.get('psar', {})
    supertrend = data.get('supertrend', {})
    cci = data.get('cci', {})
    hma = data.get('hma', {})
    willr = data.get('willr', {})
    mom = data.get('mom', {})
    stochrsi = data.get('stochrsi', {})
    ultosc = data.get('ultosc', {})
    stochf = data.get('stochf', {})
    stoch = data.get('stoch', {})
    adx = data.get('adx', {})
    ao = data.get('ao', {})
    
    signals = {
        'bbands': '看跌' if bbands.get('valueLowerBand', 0) > current_price else '看涨',  # 布林带
        'dmi': '看涨' if dmi.get('adx', 0) > 25 and dmi.get('pdi', 0) > dmi.get('mdi', 0) else '看跌',  # 定向运动指数
        'roc': '看涨' if roc.get('value', 0) > 0 else '看跌',  # 变动率
        'psar': '看跌' if psar.get('value', 0) > current_price else '看涨',  # 抛物线转向
        'supertrend': '看涨' if supertrend.get('valueAdvice', '') == 'long' else '看跌',  # 超级趋势
        'cci': '看涨' if cci.get('value', 0) > 100 else '看跌',  # 商品通道指数
        'hma': '看涨' if hma.get('value', 0) > current_price else '看跌',  # 霍尔移动平均线
        'willr': '看涨' if willr.get('value', 0) > -50 else '看跌',  # 威廉指标
        'mom': '看涨' if mom.get('value', 0) > 0 else '看跌',  # 动量指标
        'stochrsi': '看涨' if stochrsi.get('valueFastK', 0) > stochrsi.get('valueFastD', 0) else '看跌',  # 随机相对强弱指数
        'ultosc': '看涨' if ultosc.get('value', 0) > 50 else '看跌',  # 终极震荡指标
        'stochf': '看涨' if stochf.get('valueFastK', 0) > stochf.get('valueFastD', 0) else '看跌',  # 快速随机指标
        'stoch': '看涨' if stoch.get('valueK', 0) > stoch.get('valueD', 0) else '看跌',  # 随机指标
        'adx': '看涨' if adx.get('value', 0) > 25 else '看跌',  # 平均定向指数
        'ao': '看涨' if ao.get('value', 0) > 0 else '看跌'  # 雄伟振荡器
    }
    
    total_signals = len(signals)
    bullish_signals = sum(1 for signal in signals.values() if signal == '看涨')
    bearish_signals = total_signals - bullish_signals

    bullish_percentage = (bullish_signals / total_signals) * 100
    bearish_percentage = (bearish_signals / total_signals) * 100

    return bullish_percentage, bearish_percentage, signals

def main():
    while True:
        for symbol in SYMBOLS:
            market_data = get_market_data(symbol)
            market_data = calculate_macd_rsi(market_data)
            
            if market_data.empty:
                continue

            last_macd = market_data.iloc[-1]['macd']
            last_signal = market_data.iloc[-1]['signal']
            prev_macd = market_data.iloc[-2]['macd']
            prev_signal = market_data.iloc[-2]['signal']
            
            # 检查是否有金叉或死叉
            if (prev_macd < prev_signal and last_macd > last_signal) or (prev_macd > prev_signal and last_macd < last_signal):
                current_price = fetch_current_price(symbol)
                if current_price is None:
                    continue
                
                indicators = [
                    'bbands', 'dmi', 'roc', 'psar', 'supertrend',
                    'cci', 'hma', 'willr', 'mom', 'stochrsi', 
                    'ultosc', 'stochf', 'stoch', 'adx', 'ao'
                ]
                
                data = {}
                for indicator in indicators:
                    data[indicator] = fetch_taapi_data(indicator, symbol)
                
                bullish_percentage, bearish_percentage, signals = analyze_market(data, current_price)
                
                message = f"Symbol: {symbol}\nCurrent Price: {current_price}\n\n" \
                          f"Bullish Signals: {bullish_percentage:.2f}%\nBearish Signals: {bearish_percentage:.2f}%\n\n" \
                          f"Signals:\n" + "\n".join([f"{ind}: {sig}" for ind, sig in signals.items()])

                send_telegram_message(message)
        
        # 每5分钟检查一次
        time.sleep(300)

if __name__ == "__main__":
    main()
