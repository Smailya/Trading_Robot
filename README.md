
I developed a Trading_Robot which is based on Python bot for automated crypto trading on the VALR exchange 🚀. It uses technical indicators and a robust risk management strategy to execute trades based on set conditions. Includes a Flask web dashboard for real-time monitoring of bot activity and performance 📊.

Features
Automated Trading: Executes buy and sell orders based on technical analysis indicators such as Moving Averages (MA), Relative Strength Index (RSI), and Moving Average Convergence Divergence (MACD).
Risk Management: Implements strict risk management rules, including position sizing and dynamic stop-loss and take-profit levels.
Backtesting: Allows for historical backtesting of trading strategies to evaluate performance before live trading.
Real-time Monitoring: Flask web application to display real-time trading activity, historical actions, and performance metrics.
Logging: Comprehensive logging of all trading actions and errors to facilitate debugging and performance evaluation.

Installation
Clone the repository:
bash
Copier le code
git clone https://github.com/yourusername/Trading_Robot.git
cd Trading_Robot
Create and activate a virtual environment:
bash
Copier le code
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Install dependencies:
pip install -r requirements.txt
pip install requests python-dotenv Flask pandas
Create a .env file and add your VALR API credentials:
.env file
VALR_API_KEY=your_api_key
VALR_SECRET_KEY=your_secret_key
Usage
Run the Flask web application:
python app.py
Start the trading bot:
python trading_bot.py
Files and Directories
app.py: The main Flask application file for the web dashboard.
trading_bot.py: The core trading bot logic.
requirements.txt: List of Python dependencies.
historical_actions.json: JSON file to store historical trade actions.
trading_bot.log: Log file for bot activity.
Technical Indicators
MA50: 50-period Moving Average
MA200: 200-period Moving Average
RSI: 14-period Relative Strength Index
MACD: Moving Average Convergence Divergence with 12, 26, and 9 periods
Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes. Ensure your code adheres to the project's coding standards and is well-documented.

License
This project is licensed under the MIT License. See the LICENSE file for details.

