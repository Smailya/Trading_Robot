# Automated Cryptocurrency Trading Bot

## Overview

This project is an automated cryptocurrency trading bot that leverages advanced technical indicators such as **RSI (Relative Strength Index)** and **MACD (Moving Average Convergence Divergence)** to execute trades in real-time. It features a user-friendly dashboard built with **Flask** and integrates email notifications to alert users of important trading signals.

## Features

- Real-time trade execution based on RSI and MACD indicators
- Flask-powered dashboard for monitoring trades and bot status
- Email notifications to keep users informed about trading signals and actions
- Backend automation handling asynchronous tasks for timely operations
- Modular design for easy extension and customization

## Why This Matters

This project demonstrates how full-stack engineers can combine financial algorithms with real-time backend automation - a crucial capability in fintech platforms. It provides practical experience in:

- Developing trading algorithms using technical indicators
- Building interactive web dashboards with Flask
- Managing asynchronous operations for real-time responsiveness
- Implementing notification systems to enhance user engagement

These skills are highly valuable for companies developing intelligent automation tools, trading systems, or financial dashboards that support quick decision-making and seamless operations.

## Getting Started

### Prerequisites

- Python 3.x
- Flask
- Libraries for technical analysis (e.g., `ta-lib` or `pandas_ta`)
- Email sending library (e.g., `smtplib` or third-party services)

Install required packages via pip:

pip install flask pandas ta-lib

text

### How to Use

1. Clone the repository:
git clone https://github.com/yourusername/your-repo-name.git

text
2. Navigate to the project directory:
cd your-repo-name

text
3. Configure your trading API credentials and email settings in the configuration file.
4. Run the Flask dashboard:
python app.py

text
5. The bot will start monitoring the market, executing trades, and sending email alerts based on the configured indicators.

## Example

from trading_bot import TradingBot

bot = TradingBot(api_key='YOUR_API_KEY', secret='YOUR_SECRET')
bot.start()

text

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve functionality or add features.

## License

This project is licensed under the MIT License.

---

Developed by Ismail Cisse
Bringing together finance, automation, and web technologies to build smarter trading solutions
