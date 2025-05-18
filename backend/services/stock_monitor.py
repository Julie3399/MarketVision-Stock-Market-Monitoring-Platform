from typing import List, Dict
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class StockMonitor:
    def __init__(self):
        self.alert_thresholds = {
            'daily_change': 5.0,  # 5%
            'rapid_rise': 3.0,    # 3%
            'volume_surge': 300   # 300%
        }
        self.alerts_history = {}  # Store triggered alerts to avoid duplicate notifications
        # Add cache, data valid for 60 seconds
        self.data_cache = TTLCache(maxsize=100, ttl=60)
        
    def get_stock_data(self, symbol: str) -> Dict:
        """Get stock data with cache"""
        cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
            
        stock = yf.Ticker(symbol)
        data = {
            'hist': stock.history(period='1d', interval='15m'),
            'daily_data': stock.history(period='1y'),
            'timestamp': datetime.now()
        }
        self.data_cache[cache_key] = data
        return data
        
    def check_alerts(self, symbol: str) -> Dict:
        """Check all alert conditions"""
        try:
            current_time = datetime.now()
            
            # Get data using cache
            data = self.get_stock_data(symbol)
            hist = data['hist']
            daily_data = data['daily_data']
            
            if hist.empty or daily_data.empty:
                return {
                    'symbol': symbol,
                    'alerts': [],
                    'timestamp': current_time.isoformat()
                }
            
            alerts = []
            
            # 1. Check daily price change
            daily_change = ((hist['Close'][-1] - hist['Open'][0]) / hist['Open'][0]) * 100
            if daily_change > self.alert_thresholds['daily_change']:
                alerts.append({
                    'type': 'daily_surge',
                    'message': f'Daily increase reached {daily_change:.2f}%',
                    'value': daily_change,
                    'threshold': self.alert_thresholds['daily_change']
                })
            
            # 2. Check 15-minute rapid rise
            if len(hist) >= 2:
                fifteen_min_change = ((hist['Close'][-1] - hist['Close'][-2]) / hist['Close'][-2]) * 100
                if fifteen_min_change > self.alert_thresholds['rapid_rise']:
                    alerts.append({
                        'type': 'rapid_rise',
                        'message': f'15-minute increase reached {fifteen_min_change:.2f}%',
                        'value': fifteen_min_change,
                        'threshold': self.alert_thresholds['rapid_rise']
                    })
            
            # 3. Check 52-week high
            fifty_two_week_high = daily_data['High'].max()
            current_price = hist['Close'][-1]
            if current_price >= fifty_two_week_high:
                alerts.append({
                    'type': 'new_high',
                    'message': f'Broke 52-week high: {current_price:.2f}',
                    'value': current_price,
                    'threshold': fifty_two_week_high
                })
            
            # Update alert history
            alert_key = f"{symbol}_{current_time.strftime('%Y%m%d_%H%M')}"
            if alerts and alert_key not in self.alerts_history:
                self.alerts_history[alert_key] = alerts
            
            return {
                'symbol': symbol,
                'alerts': alerts,
                'timestamp': current_time.isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking alerts for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'alerts': [],
                'timestamp': current_time.isoformat(),
                'error': str(e)
            }
