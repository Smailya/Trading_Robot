import os
import time
import hashlib
import hmac
import logging
import pandas as pd
import requests
import json
from datetime import datetime
from requests.exceptions import RequestException
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['DEBUG'] = True  # Enable debug mode

# Load VALR API credentials from environment variables
API_KEY = os.getenv('VALR_API_KEY')
SECRET_KEY = os.getenv('VALR_SECRET_KEY')
BASE_URL = 'your base url'


# Constants for risk management
RISK_PER_TRADE = 0.01
MAX_OPEN_POSITIONS = 3
STOP_LOSS_FACTOR = 1.5
TAKE_PROFIT_FACTOR = 2

# Logging setup
log_file_path = 'trading_bot.log'
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,  # Set logging to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Historical actions storage
historical_actions = []

def generate_signature(api_secret, timestamp, verb, path, body=""):
    """Generate HMAC SHA512 signature."""
    message = f"{timestamp}{verb.upper()}{path}{body}"
    logging.debug(f"Message to sign: {message}")
    signature = hmac.new(bytearray(api_secret, 'utf-8'), message.encode('utf-8'), hashlib.sha512).hexdigest()
    logging.debug(f"Generated signature: {signature}")
    return signature

def authenticate(verb, path, body=""):
    """Generate headers for API authentication."""
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(SECRET_KEY, timestamp, verb, path, body)
    headers = {
        'X-VALR-API-KEY': API_KEY,
        'X-VALR-API-SIGNATURE': signature,
        'X-VALR-API-TIMESTAMP': timestamp,
        'Content-Type': 'application/json'
    }
    logging.debug(f"Headers: {headers}")
    return headers

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html', historical_actions=historical_actions)

@app.route('/api/trades', methods=['GET'])
def fetch_trades():
    """Fetch trades from the API."""
    try:
        response = requests.get(BASE_URL + 'account/trades', headers=authenticate('GET', '/v1/account/trades'))
        response.raise_for_status()
        trade_data = response.json()
        return jsonify(trade_data)
    except RequestException as e:
        logging.error(f"Error fetching trades: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance')
def performance():
    """Fetch account balance from the API."""
    try:
        response = requests.get(BASE_URL + 'account/balance', headers=authenticate('GET', '/v1/account/balance'))
        response.raise_for_status()
        balance_data = response.json()
        return jsonify(balance_data)
    except RequestException as e:
        logging.error(f"Error fetching balance: {e}")
        return jsonify({'initial_balance': 10000, 'current_balance': 10000, 'profit_loss': 0})

@app.route('/api/historical_actions')
def api_historical_actions():
    """Return historical actions."""
    return jsonify(historical_actions)

def get_market_data():
    """Fetch market data from the API."""
    try:
        response = requests.get(BASE_URL + 'public/markets/BTCZAR/ticker', headers=authenticate('GET', '/v1/public/markets/BTCZAR/ticker'))
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error fetching market data: {e}")
        return None

def get_historical_data():
    """Fetch historical data from the API."""
    try:
        response = requests.get(BASE_URL + 'public/markets/BTCZAR/candles', headers=authenticate('GET', '/v1/public/markets/BTCZAR/candles'))
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error fetching historical data: {e}")
        return None

def calculate_atr(data):
    """Calculate the Average True Range (ATR)."""
    df = pd.DataFrame(data)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    
    true_range = df[['high', 'low']].diff().abs().sum(axis=1)
    df['ATR'] = true_range.rolling(window=14).mean()
    return df['ATR'].iloc[-1]

def calculate_position_size(account_balance, risk_per_trade, entry_price, stop_loss):
    """Calculate the position size based on risk management."""
    position_size = (account_balance * risk_per_trade) / (entry_price - stop_loss)
    return position_size

def calculate_stop_loss(entry_price, atr):
    """Calculate stop loss based on entry price and ATR."""
    stop_loss = entry_price - (atr * STOP_LOSS_FACTOR)
    return stop_loss

def calculate_take_profit(entry_price, atr):
    """Calculate take profit based on entry price and ATR."""
    take_profit = entry_price + (atr * TAKE_PROFIT_FACTOR)
    return take_profit

def calculate_indicators(data):
    """Calculate trading indicators."""
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

def log_trade(action, order_type, amount, entry_price, stop_loss, take_profit):
    """Log trade actions."""
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
    """Save historical actions to a JSON file."""
    with open('historical_actions.json', 'w') as f:
        json.dump(historical_actions, f)

def backtest_strategy(historical_data):
    """Backtest the trading strategy on historical data."""
    logging.info("Starting backtest...")
    account_balance = 10000
    trades = []
    df = pd.DataFrame(historical_data['data'])
    indicators = calculate_indicators(historical_data['data'])
    atr = calculate_atr(historical_data['data'])

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

    logging.info(f"Backtest completed. Final balance: {account_balance}")
    return trades

def run_bot():
    """Run the trading bot."""
    while True:
        try:
            market_data = get_market_data()
            historical_data = get_historical_data()

            if market_data and historical_data:
                latest_price = market_data['lastTradedPrice']
                atr = calculate_atr(historical_data['data'])
                position_size = calculate_position_size(10000, RISK_PER_TRADE, latest_price, calculate_stop_loss(latest_price, atr))
                stop_loss = calculate_stop_loss(latest_price, atr)
                take_profit = calculate_take_profit(latest_price, atr)

                if len(historical_actions) < MAX_OPEN_POSITIONS:
                    # Example trade execution
                    action = 'buy'
                    log_trade(action, 'market', position_size, latest_price, stop_loss, take_profit)

            time.sleep(60)  # Wait before next iteration
        except Exception as e:
            logging.error(f"Unexpected error in bot: {e}")
            time.sleep(60)

if __name__ == '__main__':
    logging.info("Starting backtest...")
    historical_data = get_historical_data()
    if historical_data:
        backtest_strategy(historical_data)
    app.run(debug=True)  # Start Flask app in debug mode
