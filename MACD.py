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

# 监控的加密货币列表，只关注比特币和以太坊
CURRENCY_IDS = ['bitcoin', 'ethereum']

# 币种缩写映射表
CURRENCY_MAP = {
    'bitcoin': 'BTC',
    'ethereum': 'ETH'
}

# Requests Session
session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'

# Logging 配置
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# 获取市场数据（1小时K线图）
def get_market_data(currency_key, limit=150):
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
            return pd.DataFrame(data['Data']['Data'])[['time', 'close', 'volumefrom']]
        else:
            logging.error(f"Unexpected response format: {data}")
            return pd.DataFrame(columns=['time', 'close', 'volumefrom'])
    except Exception as e:
        logging.error(f"Error fetching market data for {currency_key}: {e}")
        return pd.DataFrame(columns=['time', 'close', 'volumefrom'])

# 计算技术指标
def calculate_indicators(df):
    if df.empty:
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
    return df

# 准备数据用于训练
def prepare_data(df):
    df = df.dropna()
    df['price_diff'] = df['close'].diff().shift(-1)
    df['target'] = np.where(df['price_diff'] > 0, 1, 0)
    features = ['macd', 'signal', 'histogram', 'rsi', 'upper_band', 'lower_band', 'volatility', 'volume']
    return df[features], df['target']

# 获取比特币数据并计算指标
df_btc = get_market_data('bitcoin')
df_btc = calculate_indicators(df_btc)
X, y = prepare_data(df_btc)

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 随机森林分类器和参数调优
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

grid_search = GridSearchCV(RandomForestClassifier(random_state=42), param_grid, cv=3, scoring='accuracy', n_jobs=-1)
grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_

# 预测并输出分类报告
y_pred = best_model.predict(X_test)
print(classification_report(y_test, y_pred))

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

# 主要流程
def main():
    while True:
        for currency_key in CURRENCY_IDS:
            logging.info(f"Checking {currency_key} for signals...")
            df = get_market_data(currency_key)
            df = calculate_indicators(df)
            X, _ = prepare_data(df)
            if not X.empty:
                prediction = best_model.predict(X.iloc[[-1]])[0]
                last_price = df['close'].iloc[-1]
                if prediction == 1:
                    send_alert(currency_key, f"Buy signal: Price={last_price}")
                else:
                    send_alert(currency_key, f"Sell signal: Price={last_price}")

            time.sleep(10)  # Rate-limit our requests

        time.sleep(300)  # 每5分钟检查一次

if __name__ == "__main__":
    main()
