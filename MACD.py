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
BTC_TICKER = 'BTC/USDT'
ETH_TICKER = 'ETH/USDT'
INTERVAL = '1h'
YOUR_CRYPTOCOMPARE_API_KEY = "f71cf8d61d8774c76d598ad982ff4f6860d9b15777c2fb4e3e4580d3087109b5"

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
        'ETH/USDT': 'ethereum'
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
        'ETH/USDT': 'ETH'
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
    
    analysis = []
    
    if bbands.get('valueUpperBand', 0) > bbands.get('valueMiddleBand', 0) > bbands.get('valueLowerBand', 0):
        analysis.append('布林带 (BBands) 显示看涨趋势')
    else:
        analysis.append('布林带 (BBands) 显示看跌趋势')
    
    if dmi.get('adx', 0) > 25 and dmi.get('pdi', 0) > dmi.get('mdi', 0):
        analysis.append('动向指数 (DMI) 显示看涨趋势')
    else:
        analysis.append('动向指数 (DMI) 显示看跌趋势')
    
    if roc.get('value', 0) > 0:
        analysis.append('变化率 (ROC) 显示看涨趋势')
    else:
        analysis.append('变化率 (ROC) 显示看跌趋势')
    
    if psar.get('value', 0) > current_price:
        analysis.append('抛物线转向指标 (PSAR) 显示看跌趋势')
    else:
        analysis.append('抛物线转向指标 (PSAR) 显示看涨趋势')
    
    if supertrend.get('valueAdvice', '') == 'long':
        analysis.append('超级趋势 (Supertrend) 显示看涨趋势')
    else:
        analysis.append('超级趋势 (Supertrend) 显示看跌趋势')
    
    return analysis

def main():
    symbols = [BTC_TICKER, ETH_TICKER]
    indicators = ['bbands', 'dmi', 'roc', 'psar', 'supertrend']
    
    while True:
        for symbol in symbols:
            current_price = None
            try:
                current_price = fetch_current_price(symbol)
                if current_price is None:
                    raise ValueError(f"Failed to fetch current price for {symbol}")
            except Exception as e:
                logger.error(f"Failed to fetch current price for {symbol}: {e}")
                continue
            
            df = get_market_data(symbol)
            df = calculate_macd_rsi(df)
            if df.empty:
                continue

            latest = df.iloc[-1]
            previous = df.iloc[-2]

            # 检查MACD金叉和死叉信号
            if (previous['macd'] < previous['signal'] and latest['macd'] > latest['signal']) or (previous['macd'] > previous['signal'] and latest['macd'] < latest['signal']):
                data = {}
                for indicator in indicators:
                    try:
                        fetched_data = fetch_taapi_data(indicator, symbol)
                        if fetched_data:
                            data[indicator] = fetched_data
                        else:
                            logger.warning(f"No data fetched for {indicator} and {symbol}")
                    except Exception as e:
                        logger.error(f"Failed to fetch {indicator} data for {symbol}: {e}")
                    time.sleep(15)  # Wait 30 seconds before the next request
                
                analysis = analyze_market(data, current_price)
                if latest['rsi'] < 30:
                    analysis.append("RSI 超卖（买入信号）")
                elif latest['rsi'] > 70:
                    analysis.append("RSI 超买（卖出信号）")
                
                if analysis:
                    analysis.append(f"当前价格: {current_price:.2f}")
                    analysis.append(f"MACD: {latest['macd']:.2f}")
                    analysis.append(f"RSI: {latest['rsi']:.2f}")
                    message = "\n".join(analysis)
                    send_telegram_message(message)
        
        time.sleep(300)  # 每五分钟运行一次

if __name__ == "__main__":
    main()
