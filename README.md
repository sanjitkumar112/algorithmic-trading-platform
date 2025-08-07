# Multi-Strategy Algorithmic Trading Platform

A real-time algorithmic trading platform that implements three distinct trading strategies with automated risk management and email alerts.

## 🎯 **Project Overview**

This platform automatically trades cryptocurrencies, stocks, and options using mathematical algorithms. It processes real-time market data every minute, makes trading decisions using three different strategies, and sends email alerts when trades are executed.

## 📊 **Trading Strategies**

### 1. **Kernel Regression Crypto Strategy**
- **Assets:** ETC, BTC, ETH
- **Algorithm:** Non-parametric kernel regression for price prediction
- **Logic:** Calculates two regression lines and generates BUY/SELL signals when they cross
- **Why it works:** Kernel regression is more flexible than traditional moving averages and doesn't assume specific data patterns

### 2. **SPY Mean Reversion Strategy**
- **Assets:** SPY (S&P 500 ETF)
- **Algorithm:** RSI + Bollinger Bands for mean reversion
- **Logic:** BUY when oversold (RSI < 30, price below lower Bollinger Band), SELL when overbought (RSI > 70, price above upper Bollinger Band)
- **Why it works:** Mean reversion assumes extreme price movements eventually return to the average

### 3. **RSI Momentum Options Strategy**
- **Assets:** SPY, QQQ, IWM options
- **Algorithm:** RSI + Price momentum for options signals
- **Logic:** CALL signals when RSI > 50 with positive momentum, PUT signals when RSI < 50 with negative momentum
- **Why it works:** Options are leveraged instruments, so strong momentum increases probability of success

## 🔄 **Real-Time Data Processing**

### **Data Streaming Architecture**
- **Frequency:** Fetches market data every 60 seconds
- **Sources:** Primary (Robinhood API) with fallback (Yahoo Finance)
- **Processing:** ~15,000 data operations per hour across multiple symbols
- **Reliability:** Exponential backoff retry logic for API failures

## 💰 **Risk Management & Position Sizing**

### **Kelly Criterion Position Sizing**
- **Base position:** 5% of account balance per trade
- **Confidence adjustment:** 70% for crypto/stocks, 50% for options
- **Formula:** Position size = Base size × Confidence × Account balance

### **Stop Loss & Take Profit**
- **Stop Loss:** 5% below entry price
- **Take Profit:** 10% above entry price
- **Why percentage-based:** Scales with account size for consistent risk management

## 📧 **Email Alert System**

### **Trade Notifications**
- **Trigger:** Every executed trade
- **Content:** Symbol, action, quantity, price, account balance, timestamp

### **Performance Reports**
- **Frequency:** Daily summaries
- **Content:** Total trades, win/loss ratio, profit/loss, runtime statistics

## 🛠️ **Technical Implementation**

### **Technologies Used**
- **Python:** Main programming language
- **Pandas:** Data manipulation and analysis
- **NumPy:** Mathematical calculations
- **Robin-stocks:** Robinhood API integration
- **yfinance:** Yahoo Finance data (backup)
- **SMTP:** Email functionality

### **Architecture**
- **Single-file design:** Everything in one Python file for simplicity
- **Modular functions:** Each strategy is a separate function
- **Error handling:** Try-catch blocks around all API calls
- **Comprehensive logging:** Tracks all trades, errors, and performance metrics

## 🚀 **How to Run**

### **Setup**
1. Install dependencies:
```bash
pip install -r simple_requirements.txt
```

2. Edit configuration in `simple_trading_platform.py`:
```python
ROBINHOOD_USERNAME = "your_email@example.com"
ROBINHOOD_PASSWORD = "your_password"
EMAIL_USERNAME = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
ALERT_EMAIL = "alerts@example.com"
```

3. Run the platform:
```bash
python simple_trading_platform.py
```

### **What Happens When You Run It**
1. Logs into Robinhood
2. Sends startup email notification
3. Starts monitoring ETC and SPY every 60 seconds
4. Executes trades when signals are generated
5. Sends email alerts for each trade
6. Logs performance every 10 minutes
7. Sends shutdown report when stopped

## 📈 **Performance Tracking**

### **What Gets Tracked**
- Total number of trades executed
- Win/loss ratio
- Total profit/loss
- Data processing statistics
- Runtime hours
- Error rates

### **Logging System**
- Every trade execution
- API errors and retries
- Performance metrics every 10 ticks
- Startup and shutdown events

## 🚨 **Important Disclaimers**

### **Risk Warning**
This is for educational purposes only. Trading involves substantial risk of loss. Only use small amounts of money and thoroughly test the system before using real funds.

### **Legal Considerations**
Only trade with your own money in a personal account. Do not manage other people's money or provide financial advice.

### **Technical Limitations**
This is a simplified implementation. Professional trading systems are much more sophisticated with additional safety measures, compliance features, and risk controls.

## 📚 **Documentation**

