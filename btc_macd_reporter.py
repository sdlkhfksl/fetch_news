import requests
import time
import ccxt
import numpy as np
import pandas as pd

# Telegram Bot Configuration
TELEGRAM_API_URL = 'https://api.telegram.org'
BOT_TOKEN = '5959250165:AAF5Xh6hLIEndRY9YzjsmMuCJwJwTsMFa8M'
CHAT_ID = '1640026631'

# CCXT Configuration
exchange = ccxt.binance()

def send_telegram_message(message):
    """Send a message to Telegram"""
    url = f"{TELEGRAM_API_URL}/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses
        print(f"Message sent successfully: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")
    return response.json()

def fetch_ohlc_data(symbol, timeframe='1d', limit=100):
    """Fetch OHLC data from CCXT"""
    try:
        ohlc_data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        print(f"Fetched OHLC data: {ohlc_data[:5]}...")  # Print first 5 rows for debugging
        return ohlc_data
    except Exception as e:
        print(f"Error fetching OHLC data: {e}")
        return []

def calculate_macd(df):
    """Calculate MACD indicators"""
    df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['Signal']
    print(f"MACD calculations: {df[['MACD', 'Signal', 'MACD_Histogram']].tail()}")  # Print last few rows for debugging
    return df

def generate_report(df):
    """Generate trading report based on MACD analysis"""
    last_row = df.iloc[-1]
    second_last_row = df.iloc[-2]

    macd_line = last_row['MACD']
    signal_line = last_row['Signal']
    macd_histogram = last_row['MACD_Histogram']
    
    analysis = []

    # MACD Line and Signal Line Analysis
    if macd_line > signal_line:
        if macd_line > 0:
            analysis.append("MACD线高于信号线，且两者都在0轴上方: 看涨信号，市场显示出强劲的买盘动能。")
        else:
            analysis.append("MACD线高于信号线，且两者都在0轴下方: 看跌信号，市场在下跌趋势中，但买盘动能相对较强。")
    else:
        if macd_line > 0:
            analysis.append("MACD线低于信号线，且两者都在0轴上方: 看跌信号，市场虽然在上升趋势中，但动能减弱。")
        else:
            analysis.append("MACD线低于信号线，且两者都在0轴下方: 看跌信号，市场处于下跌趋势中，卖盘动能强。")
    
    # MACD Line and Signal Line Crossovers
    if second_last_row['MACD'] <= second_last_row['Signal'] and macd_line > signal_line:
        if macd_line > 0 and signal_line > 0:
            analysis.append("MACD线从下方穿越信号线，并且两者穿越0轴: 看涨信号，可能会开始上涨。")
        else:
            analysis.append("MACD线从下方穿越信号线: 看涨信号，市场可能开始上涨。")
    
    if second_last_row['MACD'] >= second_last_row['Signal'] and macd_line < signal_line:
        if macd_line < 0 and signal_line < 0:
            analysis.append("MACD线从上方穿越信号线，并且两者穿越0轴: 看跌信号，可能会开始下跌。")
        else:
            analysis.append("MACD线从上方穿越信号线: 看跌信号，市场可能开始下跌。")

    # Cross Signals
    if second_last_row['MACD'] <= second_last_row['Signal'] and macd_line > signal_line:
        analysis.append("金叉: MACD线从下方穿越信号线，通常是买入信号。")
    
    if second_last_row['MACD'] >= second_last_row['Signal'] and macd_line < signal_line:
        analysis.append("死叉: MACD线从上方穿越信号线，通常是卖出信号。")
    
    # Trend Strength
    if abs(macd_histogram) > abs(second_last_row['MACD_Histogram']):
        analysis.append("MACD线与信号线的距离增加: 当前趋势动能在加强。")
    else:
        analysis.append("MACD线与信号线的距离减小: 当前趋势动能在减弱，可能会发生反转。")
    
    return '\n'.join(analysis)

def main():
    """Main function to fetch data, analyze and send report"""
    symbol = 'BTC/USDT'
    ohlc_data = fetch_ohlc_data(symbol, '1d', 100)
    if not ohlc_data:
        print("No data fetched, skipping analysis.")
        return

    df = pd.DataFrame(ohlc_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    df = calculate_macd(df)
    report = generate_report(df)
    
    send_telegram_message(report)

if __name__ == '__main__':
    while True:
        main()
        time.sleep(60 * 60 * 24)  # Run once a day
