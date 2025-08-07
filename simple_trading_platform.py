#!/usr/bin/env python3
"""
Multi-Strategy Algorithmic Trading Platform
"""

import robin_stocks.robinhood as r
import pandas as pd
import numpy as np
import yfinance as yf
import smtplib
import logging
import time
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Config:
    # Robinhood credentials
    ROBINHOOD_USERNAME = "your_email@example.com"  # Change this
    ROBINHOOD_PASSWORD = "your_password"  # Change this
    
    # Email settings for alerts
    EMAIL_USERNAME = "your_email@gmail.com"  # Change this
    EMAIL_PASSWORD = "your_app_password"  # Change this
    ALERT_EMAIL = "alerts@example.com"  # Change this
    
    # Trading parameters
    POSITION_SIZE = 0.05  # 5% of account per trade
    STOP_LOSS_PERCENTAGE = 0.05  # 5% stop loss
    TAKE_PROFIT_PERCENTAGE = 0.10  # 10% take profit
    
    # Data streaming
    STREAM_INTERVAL = 60  # Check every 60 seconds
    MAX_RETRIES = 3
    
    # Symbols to trade
    CRYPTO_SYMBOLS = ['ETC']
    STOCK_SYMBOLS = ['SPY']
    OPTIONS_SYMBOLS = []

class SimpleTradingPlatform:
    """Multi-strategy algorithmic trading platform"""
    
    def __init__(self):
        self.config = Config()
        self.logger = self.setup_logging()
        self.trade_count = 0
        self.total_pnl = 0.0
        self.positions = {}
        self.is_running = False
        
        # Performance tracking
        self.winning_trades = 0
        self.losing_trades = 0
        self.data_ticks = 0
        
    def setup_logging(self):
        """Setup basic logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_platform.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger("trading_platform")
    
    def login_to_robinhood(self):
        """Login to Robinhood"""
        try:
            r.login(username=self.config.ROBINHOOD_USERNAME, 
                   password=self.config.ROBINHOOD_PASSWORD)
            self.logger.info("✅ Logged into Robinhood")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to login: {e}")
            return False
    
    def get_account_info(self):
        """Get basic account information"""
        try:
            account = r.profiles.load_account_profile()
            portfolio = r.profiles.load_portfolio_profile()
            
            return {
                'cash': float(account.get('cash', 0)),
                'buying_power': float(account.get('buying_power', 0)),
                'portfolio_value': float(portfolio.get('equity', 0))
            }
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return {'cash': 0, 'buying_power': 0, 'portfolio_value': 0}
    
    def fetch_market_data(self, symbol):
        """Fetch market data"""
        try:
            # Try Robinhood first
            if symbol in self.config.CRYPTO_SYMBOLS:
                data = r.crypto.get_crypto_historicals(symbol, interval='hour', span='week')
            else:
                data = r.stocks.get_stock_historicals(symbol, interval='hour', span='week')
            
            if data:
                df = pd.DataFrame(data)
                df['close'] = pd.to_numeric(df['close_price'], errors='coerce')
                df['volume'] = pd.to_numeric(df.get('volume', 0), errors='coerce')
                return df.dropna()
            
            # Fallback to yfinance
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1wk", interval="1h")
            if not df.empty:
                df = df.reset_index()
                df['close'] = df['Close']
                df['volume'] = df['Volume']
                return df[['close', 'volume']]
                
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
        
        return None
    
    def kernel_regression_strategy(self, df):
        """Kernel regression strategy"""
        if len(df) < 10:
            return None
        
        # Kernel regression implementation
        def kernel_regression(prices, h=3.0, r=15.75):
            if len(prices) < 6:
                return prices[-1] if len(prices) > 0 else 0
            
            weights = [(1 + (i**2 / (2 * h**2 * r)))**-r for i in range(min(6, len(prices)))]
            weighted_sum = sum(prices[i] * weights[i] for i in range(len(weights)))
            return weighted_sum / sum(weights)
        
        # Calculate regression lines
        df['regression1'] = df['close'].rolling(6).apply(
            lambda x: kernel_regression(x[::-1].values), raw=True
        )
        df['regression2'] = df['close'].rolling(6).apply(
            lambda x: kernel_regression(x[::-1].values, h=1.0), raw=True
        )
        
        # Generate signals
        if len(df) >= 2:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Buy signal
            if (latest['regression1'] > latest['regression2'] and 
                prev['regression1'] <= prev['regression2']):
                return 'BUY'
            
            # Sell signal
            elif (latest['regression1'] < latest['regression2'] and 
                  prev['regression1'] >= prev['regression2']):
                return 'SELL'
        
        return None
    
    def spy_mean_reversion_strategy(self, df):
        """SPY mean reversion strategy"""
        if len(df) < 20:
            return None
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate Bollinger Bands
        df['sma'] = df['close'].rolling(20).mean()
        df['std'] = df['close'].rolling(20).std()
        df['upper_band'] = df['sma'] + (df['std'] * 2)
        df['lower_band'] = df['sma'] - (df['std'] * 2)
        
        if len(df) >= 2:
            latest = df.iloc[-1]
            
            # Buy signal (oversold)
            if (latest['rsi'] < 30 and latest['close'] < latest['lower_band']):
                return 'BUY'
            
            # Sell signal (overbought)
            elif (latest['rsi'] > 70 and latest['close'] > latest['upper_band']):
                return 'SELL'
        
        return None
    
    def rsi_momentum_strategy(self, df):
        """RSI momentum strategy for options"""
        if len(df) < 14:
            return None
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate momentum
        df['momentum'] = df['close'].pct_change(5)
        
        if len(df) >= 2:
            latest = df.iloc[-1]
            
            # Strong momentum signals
            if latest['rsi'] > 50 and latest['momentum'] > 0.02:
                return 'CALL'  # Buy call options
            
            elif latest['rsi'] < 50 and latest['momentum'] < -0.02:
                return 'PUT'   # Buy put options
        
        return None
    
    def calculate_position_size(self, signal, account_balance):
        """Calculate position size using Kelly Criterion"""
        # Base position size
        base_size = self.config.POSITION_SIZE
        
        # Confidence adjustment based on signal type
        if signal in ['BUY', 'SELL']:
            confidence = 0.7  # 70% confidence
        else:
            confidence = 0.5  # 50% confidence for options
        
        # Calculate final position size
        position_size = base_size * confidence
        dollar_amount = position_size * account_balance
        
        return dollar_amount
    
    def execute_trade(self, symbol, action, quantity, price):
        """Execute trade with exponential backoff"""
        max_retries = self.config.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                if symbol in self.config.CRYPTO_SYMBOLS:
                    if action == 'BUY':
                        order = r.orders.order_buy_crypto_limit(symbol, quantity, price)
                    else:
                        order = r.orders.order_sell_crypto_limit(symbol, quantity, price)
                else:
                    if action == 'BUY':
                        order = r.orders.order_buy_stock_limit(symbol, quantity, price)
                    else:
                        order = r.orders.order_sell_stock_limit(symbol, quantity, price)
                
                if order and 'id' in order:
                    self.logger.info(f"✅ {action} order placed for {quantity} {symbol} at ${price}")
                    return True
                
            except Exception as e:
                self.logger.warning(f"Trade attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    def send_email_alert(self, subject, message):
        """Send email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_USERNAME
            msg['To'] = self.config.ALERT_EMAIL
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
            
            text = msg.as_string()
            server.sendmail(self.config.EMAIL_USERNAME, self.config.ALERT_EMAIL, text)
            server.quit()
            
            self.logger.info("📧 Email alert sent")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def process_strategy(self, symbol, strategy_func):
        """Process a single strategy"""
        try:
            # Fetch data
            df = self.fetch_market_data(symbol)
            if df is None or len(df) < 10:
                return
            
            # Generate signal
            signal = strategy_func(df)
            if signal is None:
                return
            
            # Get account info
            account_info = self.get_account_info()
            current_price = df['close'].iloc[-1]
            
            # Calculate position size
            dollar_amount = self.calculate_position_size(signal, account_info['buying_power'])
            quantity = dollar_amount / current_price if current_price > 0 else 0
            
            if quantity > 0:
                # Execute trade
                success = self.execute_trade(symbol, signal, quantity, current_price)
                
                if success:
                    # Send email alert
                    alert_message = f"""
                    Trade Executed:
                    Symbol: {symbol}
                    Action: {signal}
                    Quantity: {quantity:.4f}
                    Price: ${current_price:.2f}
                    Account Balance: ${account_info['buying_power']:.2f}
                    Time: {datetime.now()}
                    """
                    
                    self.send_email_alert(f"Trade Alert: {signal} {symbol}", alert_message)
                    
                    # Update tracking
                    self.trade_count += 1
                    self.logger.info(f"Trade {self.trade_count}: {signal} {quantity} {symbol}")
                    
        except Exception as e:
            self.logger.error(f"Error processing strategy for {symbol}: {e}")
    
    def run(self):
        """Main trading loop"""
        self.logger.info("🚀 Starting Simple Trading Platform")
        
        if not self.login_to_robinhood():
            return
        
        self.is_running = True
        start_time = datetime.now()
        
        # Send startup notification
        self.send_email_alert(
            "Trading Platform Started", 
            f"Platform started at {start_time}\nMonitoring: {self.config.CRYPTO_SYMBOLS + self.config.STOCK_SYMBOLS}"
        )
        
        while self.is_running:
            try:
                self.data_ticks += 1
                
                # Process crypto strategy
                for symbol in self.config.CRYPTO_SYMBOLS:
                    self.process_strategy(symbol, self.kernel_regression_strategy)
                
                # Process stock strategy
                for symbol in self.config.STOCK_SYMBOLS:
                    self.process_strategy(symbol, self.spy_mean_reversion_strategy)
                
                # Log performance every 10 ticks
                if self.data_ticks % 10 == 0:
                    runtime = datetime.now() - start_time
                    self.logger.info(f"Tick {self.data_ticks}: {self.trade_count} trades, "
                                   f"Runtime: {runtime.total_seconds()/3600:.1f} hours")
                
                # Wait for next interval
                time.sleep(self.config.STREAM_INTERVAL)
                
            except KeyboardInterrupt:
                self.logger.info("Received interrupt, stopping...")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(self.config.STREAM_INTERVAL)
        
        # Send shutdown notification
        runtime = datetime.now() - start_time
        self.send_email_alert(
            "Trading Platform Stopped",
            f"Platform stopped at {datetime.now()}\n"
            f"Total trades: {self.trade_count}\n"
            f"Data ticks: {self.data_ticks}\n"
            f"Runtime: {runtime.total_seconds()/3600:.1f} hours"
        )
        
        self.logger.info("✅ Trading platform stopped")

def main():
    """Main entry point"""
    print("=" * 60)
    print(" Multi-Strategy Trading Platform")
    print("=" * 60)
    
    platform = SimpleTradingPlatform()
    platform.run()

if __name__ == "__main__":
    main() 