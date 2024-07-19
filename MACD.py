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

# 获取UTC+8时间戳
def get_utc_plus_8_time():
    utc_plus_8 = datetime.utcnow() + timedelta(hours=8)
    return utc_plus_8.strftime('%Y-%m-%d %H:%M:%S')

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

def calculate_indicators(df):
    if df.empty:
        logger.warning("Dataframe is empty. Skipping indicator calculation.")
        return df
    df['fast_ema'] = df['close'].ewm(span=12, adjust=False).mean()
    df['slow_ema'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['fast_ema'] - df['slow_ema']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['histogram'] = df['macd'] - df['signal']
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
        analysis.append('BBands indicate a Bullish trend')
    else:
        analysis.append('BBands indicate a Bearish trend')
    
    if dmi.get('adx', 0) > 25 and dmi.get('pdi', 0) > dmi.get('mdi', 0):
        analysis.append('DMI indicates a Bullish trend')
    else:
        analysis.append('DMI indicates a Bearish trend')
    
    if roc.get('value', 0) > 0:
        analysis.append('ROC indicates a Bullish trend')
    else:
        analysis.append('ROC indicates a Bearish trend')
    
    if psar.get('value', 0) > current_price:
        analysis.append('PSAR indicates a Bearish trend')
    else:
        analysis.append('PSAR indicates a Bullish trend')
    
    if supertrend.get('valueAdvice', '') == 'long':
        analysis.append('Supertrend indicates a Bullish trend')
    else:
        analysis.append('Supertrend indicates a Bearish trend')
    
    return analysis

def main():
    symbols = [BTC_TICKER, ETH_TICKER]
    indicators = ['bbands', 'dmi', 'roc', 'psar', 'supertrend']
    
    for symbol in symbols:
        data = {}
        current_price = None
        
        try:
            current_price = fetch_current_price(symbol)
            if current_price is None:
                raise ValueError(f"Failed to fetch current price for {symbol}")
        except Exception as e:
            logger.error(f"Failed to fetch current price for {symbol}: {e}")
            continue

        for indicator in indicators:
            try:
                fetched_data = fetch_taapi_data(indicator, symbol)
                if fetched_data:
                    data[indicator] = fetched_data
                else:
                    logger.warning(f"No data fetched for {indicator} and {symbol}")
            except Exception as e:
                logger.error(f"Failed to fetch {indicator} data for {symbol}: {e}")
            time.sleep(30)  # Wait 30 seconds before the next request
        
        analysis = analyze_market(data, current_price)

        # Fetch and analyze MACD and RSI
        df = get_market_data(symbol)
        df = calculate_indicators(df)
        if not df.empty:
            latest = df.iloc[-1]
            previous = df.iloc[-2]

            # MACD 交叉信号
            signals = []
            if previous['macd'] < previous['signal'] and latest['macd'] > latest['signal']:
                signals.append("MACD 交叉（买入信号）")
            elif previous['macd'] > previous['signal'] and latest['macd'] < latest['signal']:
                signals.append("MACD 交叉（卖出信号）")
            
            # RSI 解读
            if latest['rsi'] < 30:
                signals.append("RSI 超卖（买入信号）")
            elif latest['rsi'] > 70:
                signals.append("RSI 超买（卖出信号）")

            if signals:
                signals.append(f"当前价格: {current_price}")
                signals.append(f"RSI: {latest['rsi']:.2f}")
                analysis.extend(signals)
        
        if analysis:
            message = "; ".join(analysis)
            send_telegram_message(message)

if __name__ == "__main__":
    main()
