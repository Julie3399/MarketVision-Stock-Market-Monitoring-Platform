from typing import List, Dict
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

class StockScanner:
    def __init__(self):
        self.market_cap_threshold = 5_000_000_000  # 5 billion USD
        self.volume_surge_threshold = 300  # 300%
        self.institutional_ownership_threshold = 5.0  # 5%
        
    def scan_market(self) -> List[Dict]:
        """Scan the entire market for stocks meeting the criteria"""
        # Get list of NASDAQ stocks (example using subset)
        symbols = ["AAPL", "MSFT", "NVDA", "AMD", "TSLA", "MARA", "RIOT", "COIN"]
        results = []
        
        for symbol in symbols:
            try:
                stock_data = self.analyze_stock(symbol)
                if stock_data and self.check_conditions(stock_data):
                    results.append(self.generate_report(stock_data))
            except Exception as e:
                print(f"Error analyzing {symbol}: {str(e)}")
                continue
                
        return results
    
    def analyze_stock(self, symbol: str) -> Dict:
        """Analyze all relevant data for a single stock"""
        stock = yf.Ticker(symbol)
        
        # Get historical data
        hist = stock.history(period='60d')  # Get 60 days of data for average calculation
        if hist.empty:
            return None
            
        # Get company info
        info = stock.info
        
        return {
            'symbol': symbol,
            'history': hist,
            'info': info,
            'institutional_ownership': self.get_institutional_ownership(symbol),
            'market_cap': info.get('marketCap', float('inf')),
            'current_volume': hist['Volume'][-1],
            'avg_volume_30d': hist['Volume'][-30:].mean(),
            'price': hist['Close'][-1],
            'price_change': ((hist['Close'][-1] - hist['Close'][-2]) / hist['Close'][-2]) * 100,
            'volume_change': ((hist['Volume'][-1] - hist['Volume'][-2]) / hist['Volume'][-2]) * 100
        }
    
    def check_conditions(self, stock_data: Dict) -> bool:
        """Check if stock meets all conditions"""
        conditions = {
            'volume_surge': self.check_volume_surge(stock_data),
            'not_trending': self.check_not_trending(stock_data['symbol']),
            'low_institutional': self.check_institutional_ownership(stock_data),
            'small_cap': self.check_market_cap(stock_data),
            'technical_breakout': self.check_technical_breakout(stock_data)
        }
        
        return all(conditions.values())
    
    def check_volume_surge(self, stock_data: Dict) -> bool:
        """Check if volume has surged over 300%"""
        volume_ratio = (stock_data['current_volume'] / stock_data['avg_volume_30d']) * 100
        return volume_ratio > self.volume_surge_threshold
    
    def check_not_trending(self, symbol: str) -> bool:
        """Check if stock is not on trending list (can be adjusted based on data source)"""
        # Example implementation, should query actual trending stocks list
        trending_symbols = self.get_trending_stocks()
        return symbol not in trending_symbols
    
    def get_trending_stocks(self) -> List[str]:
        """Get list of trending stocks (example implementation)"""
        # Actual implementation should get from reliable data source
        return ["AAPL", "MSFT", "GOOGL"]  # Example trending stocks
    
    def check_institutional_ownership(self, stock_data: Dict) -> bool:
        """Check if institutional ownership is below threshold"""
        return stock_data['institutional_ownership'] < self.institutional_ownership_threshold
    
    def get_institutional_ownership(self, symbol: str) -> float:
        """Get institutional ownership percentage"""
        try:
            stock = yf.Ticker(symbol)
            # Should get from more reliable data source
            return stock.info.get('institutionalOwnership', 0) * 100
        except:
            return 0
    
    def check_market_cap(self, stock_data: Dict) -> bool:
        """Check if stock is small cap"""
        return stock_data['market_cap'] < self.market_cap_threshold
    
    def check_technical_breakout(self, stock_data: Dict) -> bool:
        """Check for technical breakout"""
        hist = stock_data['history']
        
        # Calculate technical indicators
        # 1. Break above 20-day moving average
        ma20 = hist['Close'].rolling(window=20).mean()
        price_above_ma = hist['Close'][-1] > ma20[-1]
        
        # 2. RSI indicator
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_bullish = rsi[-1] > 50 and rsi[-1] < 70
        
        # 3. Volume confirmation
        volume_confirmation = hist['Volume'][-1] > hist['Volume'][-20:].mean()
        
        return price_above_ma and rsi_bullish and volume_confirmation
    
    def generate_report(self, stock_data: Dict) -> Dict:
        """Generate movement analysis report"""
        return {
            'symbol': stock_data['symbol'],
            'market_cap': stock_data['market_cap'],
            'current_price': stock_data['price'],
            'price_change': stock_data['price_change'],
            'volume_change': ((stock_data['current_volume'] / stock_data['avg_volume_30d']) - 1) * 100,
            'institutional_ownership': stock_data['institutional_ownership'],
            'analysis': {
                'technical': self.get_technical_analysis(stock_data),
                'fundamental': self.get_fundamental_analysis(stock_data),
                'news': self.get_related_news(stock_data['symbol'])
            },
            'alerts': self.get_alerts(stock_data)
        }
    
    def get_technical_analysis(self, stock_data: Dict) -> Dict:
        """Get technical analysis"""
        hist = stock_data['history']
        return {
            'ma_analysis': 'Broke above 20-day MA' if self.check_technical_breakout(stock_data) else 'No breakout',
            'volume_analysis': f"Volume increased {((stock_data['current_volume']/stock_data['avg_volume_30d'])-1)*100:.2f}% vs 30-day average",
            'price_momentum': 'Uptrend' if stock_data['price_change'] > 0 else 'Downtrend'
        }
    
    def get_fundamental_analysis(self, stock_data: Dict) -> Dict:
        """Get fundamental analysis"""
        info = stock_data['info']
        return {
            'market_cap': f"${stock_data['market_cap']/1000000000:.2f}B",
            'pe_ratio': info.get('forwardPE', 'N/A'),
            'institutional_ownership': f"{stock_data['institutional_ownership']:.2f}%"
        }
    
    def get_related_news(self, symbol: str) -> List[Dict]:
        """Get related news (example implementation)"""
        # Actual implementation should use news API
        return [
            {
                'title': f'Example News - {symbol} shows unusual activity',
                'source': 'Example News Source',
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    def get_alerts(self, stock_data: Dict) -> List[str]:
        """Generate alert messages"""
        alerts = []
        if self.check_volume_surge(stock_data):
            alerts.append(f"Volume surged {((stock_data['current_volume']/stock_data['avg_volume_30d'])-1)*100:.2f}%")
        if self.check_technical_breakout(stock_data):
            alerts.append("Technical breakout detected")
        if stock_data['institutional_ownership'] < self.institutional_ownership_threshold:
            alerts.append(f"Low institutional ownership ({stock_data['institutional_ownership']:.2f}%)")
        return alerts
