import json
import requests
import os
import time
import logging
import hashlib
import hmac
import pandas as pd
from datetime import datetime
from requests.exceptions import RequestException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('VALR_API_KEY')
SECRET_KEY = os.getenv('VALR_SECRET_KEY')
BASE_URL = 'https://api.valr.com/v1/'

# Constants for risk management
RISK_PER_TRADE = 0.01
MAX_OPEN_POSITIONS = 3
STOP_LOSS_FACTOR = 1.5
TAKE_PROFIT_FACTOR = 2

# Logging setup
log_file_path = 'trading_bot.log'
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

historical_actions = []

def sign_request(api_key_secret, timestamp, verb, path, body=""):
    payload = "{}{}{}{}".format(timestamp, verb.upper(), path, body)
    message = bytearray(payload, 'utf-8')
    signature = hmac.new(bytearray(api_key_secret, 'utf-8'), message, digestmod=hashlib.sha512).hexdigest()
    return signature

def authenticate(verb, path, body=""):
    timestamp = str(int(time.time() * 1000))
    signature = sign_request(SECRET_KEY, timestamp, verb, path, body)
    
    headers = {
        'X-VALR-API-KEY': API_KEY,
        'X-VALR-API-SIGNATURE': signature,
        'X-VALR-API-TIMESTAMP': timestamp,
        'Content-Type': 'application/json'
    }
    return headers

def get_trades():
    try:
        headers = authenticate('GET', '/account/trades')
        response = requests.get(BASE_URL + 'account/trades', headers=headers)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error fetching trades: {e}")
        if e.response:
            logging.error(f"Response content: {e.response.text}")
        return None

def get_market_data():
    try:
        response = requests.get(BASE_URL + 'public/markets/BTCZAR/ticker', headers=authenticate('GET', '/public/markets/BTCZAR/ticker'))
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error fetching market data: {e}")
        return None

def get_historical_data():
    try:
        response = requests.get(BASE_URL + 'public/markets/BTCZAR/candles', headers=authenticate('GET', '/public/markets/BTCZAR/candles'))
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error fetching historical data: {e}")
        return None

def calculate_atr(data):
    df = pd.DataFrame(data)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)

    true_range = df[['high', 'low']].diff().abs().sum(axis=1)
    df['ATR'] = true_range.rolling(window=14).mean()

    return df['ATR'].iloc[-1]

def calculate_position_size(account_balance, risk_per_trade, entry_price, stop_loss):
    position_size = (account_balance * risk_per_trade) / (entry_price - stop_loss)
    return position_size

def calculate_stop_loss(entry_price, atr):
    return entry_price - (atr * STOP_LOSS_FACTOR)

def calculate_take_profit(entry_price, atr):
    return entry_price + (atr * TAKE_PROFIT_FACTOR)

def calculate_indicators(data):
    df = pd.DataFrame(data)
    df['close'] = df['close'].astype(float)

    df['MA50'] = df['close'].rolling(window=50).mean()
    df['MA200'] = df['close'].rolling(window=200).mean()

    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    return df[['MA50', 'MA200', 'RSI', 'MACD', 'Signal']]

def get_open_positions():
    return []

def log_trade(action, order_type, amount, entry_price, stop_loss, take_profit):
    trade_info = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'order_type': order_type,
        'amount': amount,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'take_profit': take_profit
    }
    historical_actions.append(trade_info)
    logging.info(f"Trade logged: {trade_info}")

def save_historical_actions():
    with open('historical_actions.json', 'w') as f:
        json.dump(historical_actions, f)

def trading_strategy(account_balance, historical_data):
    try:
        indicators = calculate_indicators(historical_data['data'])
        atr = calculate_atr(historical_data['data'])

        trades = []
        df = pd.DataFrame(historical_data['data'])
        for index, row in df.iterrows():
            latest_close = row['close']
            ma50 = indicators['MA50'].iloc[index]
            ma200 = indicators['MA200'].iloc[index]
            rsi = indicators['RSI'].iloc[index]
            macd = indicators['MACD'].iloc[index]
            signal = indicators['Signal'].iloc[index]

            if ma50 > ma200 and rsi < 30 and macd > signal:
                logging.info("Buy signal generated.")
                position_size = calculate_position_size(account_balance, RISK_PER_TRADE, latest_close, calculate_stop_loss(latest_close, atr))
                stop_loss = calculate_stop_loss(latest_close, atr)
                take_profit = calculate_take_profit(latest_close, atr)
                trades.append(('buy', position_size, latest_close, stop_loss, take_profit))
                account_balance -= position_size * latest_close
            elif ma50 < ma200 and rsi > 70 and macd < signal:
                logging.info("Sell signal generated.")
                position_size = calculate_position_size(account_balance, RISK_PER_TRADE, latest_close, calculate_stop_loss(latest_close, atr))
                stop_loss = calculate_stop_loss(latest_close, atr)
                take_profit = calculate_take_profit(latest_close, atr)
                trades.append(('sell', position_size, latest_close, stop_loss, take_profit))
                account_balance += position_size * latest_close

        return trades, account_balance

    except Exception as e:
        logging.error(f"Unexpected error in trading strategy: {e}")

def backtest_strategy(historical_data):
    initial_balance = 10000
    final_balance = initial_balance
    trades, final_balance = trading_strategy(final_balance, historical_data)

    for trade in trades:
        log_trade(trade[0], trade[0], trade[1], trade[2], trade[3], trade[4])

    logging.info(f"Backtest complete. Initial balance: {initial_balance}, Final balance: {final_balance}")

def place_order(order_type, amount, stop_loss, take_profit):
    open_positions = get_open_positions()
    if len(open_positions) < MAX_OPEN_POSITIONS:
        order = {
            'side': order_type,
            'quantity': amount,
            'pair': 'BTCZAR',
            'stopLoss': stop_loss,
            'takeProfit': take_profit,
        }
        try:
            response = requests.post(BASE_URL + 'account/orders/market', headers=authenticate('POST', '/account/orders/market', json.dumps(order)), json=order)
            response.raise_for_status()
            logging.info(f"Order placed: {response.json()}")
            return response.json()
        except RequestException as e:
            logging.error(f"Error placing order: {e}")
            if e.response:
                logging.error(f"Response content: {e.response.text}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error placing order: {e}")
            return None
    else:
        logging.info("Maximum open positions reached. Order not placed.")
        return None

def run_bot():
    logging.info("Trading bot started.")
    while True:
        try:
            historical_data = get_historical_data()
            if historical_data:
                account_balance = 10000  # Replace with actual balance retrieval logic
                trading_strategy(account_balance, historical_data)
            time.sleep(60)  # Run every minute
        except KeyboardInterrupt:
            logging.info("Bot stopped by user.")
            save_historical_actions()
            break
        except (RequestException, ProtocolError) as e:
            logging.error(f"Network error: {e}")
            time.sleep(60)
        except Exception as e:
            logging.error(f"Unexpected error in bot: {e}")
            time.sleep(60)

if __name__ == '__main__':
    logging.info("Starting backtest...")
    historical_data = get_historical_data()
    if historical_data:
        backtest_strategy(historical_data)
    run_bot()
