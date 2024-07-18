import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report
import logging
import time

# 配置
YOUR_CRYPTOCOMPARE_API_KEY = "f71cf8d61d8774c76d598ad982ff4f6860d9b15777c2fb4e3e4580d3087109b5"
TELEGRAM_BOT_TOKEN = "5925179620:AAELdC5OfDHXqvpBNEx5xEOjCzcPdY0isck"
TELEGRAM_CHAT_ID = "1640026631"

# 监控的加密货币列表，增加BNB
CURRENCY_IDS = ['bitcoin', 'ethereum', 'binancecoin']

# 币种缩写映射表
CURRENCY_MAP = {
    'bitcoin': 'BTC',
    'ethereum': 'ETH',
    'binancecoin': 'BNB'
}

# Requests Session
session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'

# Logging 配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("macd.log"),
        logging.StreamHandler()
    ]
)

# 获取市场数据（1小时K线图）
def get_market_data(currency_key, limit=150):
    logging.info(f"Fetching market data for {currency_key}...")
    currency_id = CURRENCY_MAP[currency_key]
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
            logging.info(f"Successfully fetched market data for {currency_key}.")
            return pd.DataFrame(data['Data']['Data'])[['time', 'close', 'volumefrom']]
        else:
            logging.error(f"Unexpected response format: {data}")
            return pd.DataFrame(columns=['time', 'close', 'volumefrom'])
    except Exception as e:
        logging.error(f"Error fetching market data for {currency_key}: {e}")
        return pd.DataFrame(columns=['time', 'close', 'volumefrom'])

# 计算技术指标
def calculate_indicators(df):
    logging.info("Calculating indicators...")
    if df.empty:
        logging.warning("Dataframe is empty. Skipping indicator calculation.")
        return df
    df['fast_ema'] = df['close'].ewm(span=12, adjust=False).mean()
    df['slow_ema'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['fast_ema'] - df['slow_ema']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['histogram'] = df['macd'] - df['signal']
    df['rsi'] = 100 - (100 / (1 + df['close'].pct_change().rolling(window=14).apply(lambda x: (x[x > 0].sum() / abs(x[x <= 0].sum())), raw=True)))
    df['upper_band'] = df['close'].rolling(window=20).mean() + (df['close'].rolling(window=20).std() * 2)
    df['lower_band'] = df['close'].rolling(window=20).mean() - (df['close'].rolling(window=20).std() * 2)
    df['volatility'] = df['close'].rolling(window=10).std()
    df['volume'] = df['volumefrom']
    logging.info("Indicators calculated successfully.")
    return df

# 准备数据用于训练
def prepare_data(df):
    logging.info("Preparing data for training...")
    df = df.dropna().copy()
    df['price_diff'] = df['close'].diff().shift(-1)
    df['target'] = np.where(df['price_diff'] > 0, 1, 0)
    features = ['macd', 'signal', 'histogram', 'rsi', 'upper_band', 'lower_band', 'volatility', 'volume']
    df = df.dropna()
    logging.info("Data prepared successfully.")
    return df[features], df['target']

# 获取比特币数据并计算指标
df_btc = get_market_data('bitcoin')
df_btc = calculate_indicators(df_btc)
X, y = prepare_data(df_btc)

# 划分训练集和测试集
logging.info("Splitting data into training and testing sets...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
logging.info("Data split successfully.")

# 随机森林分类器和参数调优
logging.info("Starting grid search for RandomForest parameters...")
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

grid_search = GridSearchCV(RandomForestClassifier(random_state=42), param_grid, cv=3, scoring='accuracy', n_jobs=-1)
grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_
logging.info("Grid search completed. Best parameters found.")

# 预测并输出分类报告
logging.info("Predicting test data and generating classification report...")
y_pred = best_model.predict(X_test)
logging.info("\n" + classification_report(y_test, y_pred))

# 获取 UTC+8 时间戳
def get_utc_plus_8_time():
    utc_plus_8 = datetime.utcnow() + timedelta(hours=8)
    return utc_plus_8.strftime('%Y-%m-%d %H:%M:%S')

# 发送警报
def send_alert(currency_key, message):
    timestamp = get_utc_plus_8_time()
    full_message = f"{timestamp} - {currency_key}: {message}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": full_message
    }
    try:
        response = session.post(url, json=payload)
        if response.status_code == 200:
            logging.info("Message sent to Telegram successfully.")
        else:
            logging.error(f"Failed to send message to Telegram: {response.text}")
    except Exception as e:
        logging.error(f"Error sending alert message: {e}")

# 检查交易信号
def check_signals(df):
    logging.info("Checking for trade signals...")
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    signals = []

    # MACD 交叉信号
    if previous['macd'] < previous['signal'] and latest['macd'] > latest['signal']:
        signals.append("MACD 交叉（买入信号）")
    elif previous['macd'] > previous['signal'] and latest['macd'] < latest['signal']:
        signals.append("MACD 交叉（卖出信号）")

    # RSI 超买/超卖信号
    if latest['rsi'] < 30:
        signals.append("RSI 超卖（买入信号）")
    elif latest['rsi'] > 70:
        signals.append("RSI 超买（卖出信号）")

    # 布林带突破信号
    if latest['close'] < latest['lower_band']:
        signals.append("布林带下轨（买入信号）")
    elif latest['close'] > latest['upper_band']:
        signals.append("布林带上轨（卖出信号）")

    return signals

# 检查至少两个信号匹配
def check_matching_signals(df):
    indicators = check_signals(df)
    
    latest_features = df.iloc[-1][['macd', 'signal', 'histogram', 'rsi', 'upper_band', 'lower_band', 'volatility', 'volume']].values.reshape(1, -1)
    prediction = best_model.predict(latest_features)[0]
    prediction_signal = "模型预测价格将上涨（买入信号）" if prediction == 1 else "模型预测价格将下跌（卖出信号）"
    
    if prediction == 1:
        indicators.append("买入信号")
    else:
        indicators.append("卖出信号")
    
    buy_signals = indicators.count("买入信号") + indicators.count("MACD 交叉（买入信号）") + indicators.count("RSI 超卖（买入信号）") + indicators.count("布林带下轨（买入信号）")
    sell_signals = indicators.count("卖出信号") + indicators.count("MACD 交叉（卖出信号）") + indicators.count("RSI 超买（卖出信号）") + indicators.count("布林带上轨（卖出信号）")
    
    if buy_signals >= 2:
        return "买入信号"
    elif sell_signals >= 2:
        return "卖出信号"
    else:
        return None

# 主要流程
def main():
    while True:
        for currency_key in CURRENCY_IDS:
            logging.info(f"Checking {currency_key} for signals...")
            df = get_market_data(currency_key)
            df = calculate_indicators(df)
            signal = check_matching_signals(df)
            
            if signal:
                last_price = df['close'].iloc[-1]
                send_alert(currency_key, f"{signal}: Price={last_price}")
            
            time.sleep(10)  # Rate-limit our requests

        logging.info("Sleeping for 5 minutes before the next check.")
        time.sleep(300)  # 每5分钟检查一次

if __name__ == "__main__":
    main()
