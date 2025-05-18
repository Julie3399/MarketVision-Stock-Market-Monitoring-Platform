import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.graph_objects as go
from pathlib import Path
import logging
import pytz
import requests
from time import sleep
import random

logger = logging.getLogger(__name__)
class StockAnalyzer:
    def __init__(self):
        # Create charts directory
        self.charts_dir = Path(__file__).parent.parent / 'static' / 'charts'
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        
        # Set multiple user agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0"
        ]
        
        # Set request headers (randomly select a user agent during initialization)
        self.headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json"
        }
        
        # Add request configuration
        self.max_retries = 3
        self.base_delay = 2  # Base delay in seconds

    def get_stock_data(self, ticker, period='1y', start=None, end=None):
        """Get stock data using Yahoo Finance API (supports date range or period)"""
        retries = 0
        delay = self.base_delay
        
        while retries <= self.max_retries:
            try:
                # Randomly select a user agent before each request
                self.headers["User-Agent"] = random.choice(self.user_agents)
                
                # Add more common browser headers
                self.headers.update({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Referer": "https://finance.yahoo.com/",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Upgrade-Insecure-Requests": "1"
                })
                
                # Add random delay to avoid fixed interval requests
                sleep_time = delay + random.uniform(0.5, 1.5)
                logger.info(f"Waiting {sleep_time:.2f} seconds before requesting {ticker} data")
                sleep(sleep_time)
                
                # Prioritize explicit date range parameters
                use_date_range = start is not None or end is not None
                
                # Build base URL
                url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
                params = {
                    "interval": "1d",
                    "includePrePost": True,
                    "events": "div,splits,capitalGains"
                }

                if use_date_range:
                    # Handle date range mode
                    start_date = pd.to_datetime(start)
                    end_date = pd.to_datetime(end)
                    
                    # Convert to Unix timestamp (seconds)
                    params.update({
                        "period1": int(start_date.timestamp()),
                        "period2": int(end_date.timestamp())
                    })
                else:
                    # Handle period mode
                    period_map = {
                        '1d': '1d', '5d': '5d', '1mo': '1mo', '3mo': '3mo',
                        '6mo': '6mo', '1y': '1y', '2y': '2y', '5y': '5y', 'max': 'max'
                    }
                    params["range"] = period_map.get(period, '1y')

                # Send request
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code == 429:
                    logger.warning(f"Request for {ticker} hit rate limit (429), attempting to get data via Google proxy")
                    google_data = self.get_stock_data_via_google(ticker, period, params["interval"])
                    if google_data is not None:
                        logger.info(f"Successfully retrieved {ticker} data via Google proxy")
                        data = google_data
                        break
                    else:
                        logger.error(f"Unable to get {ticker} data via Google proxy")
                        retries += 1
                        delay *= 2  # Exponential backoff
                        logger.warning(f"Request for {ticker} hit rate limit (429), retry {retries}, waiting {delay} seconds")
                        continue
                
                if response.status_code != 200:
                    logger.error(f"Failed to get {ticker} data, status code: {response.status_code}")
                    return None

                data = response.json()
                
                try:
                    chart_data = data['chart']['result'][0]
                    timestamps = chart_data['timestamp']
                    quote = chart_data['indicators']['quote'][0]
                    
                    # Create DataFrame
                    df = pd.DataFrame({
                        'Open': quote.get('open', []),
                        'High': quote.get('high', []),
                        'Low': quote.get('low', []),
                        'Close': quote.get('close', []),
                        'Volume': quote.get('volume', [])
                    }, index=pd.to_datetime(timestamps, unit='s'))
                    
                    # Handle adjusted close price
                    if 'adjclose' in chart_data['indicators']:
                        df['Adj Close'] = chart_data['indicators']['adjclose'][0]['adjclose']
                    
                    # Clean data: remove NaN and duplicate indices
                    df = df.dropna().loc[~df.index.duplicated(keep='first')]
                    
                    # Ensure date range validity (when using start/end)
                    if use_date_range:
                        df = df.loc[start_date:end_date]
                    
                    return df

                except (KeyError, IndexError) as e:
                    logger.error(f"Failed to parse {ticker} data: {str(e)}")
                    return None
                    
            except Exception as e:
                logger.error(f"Exception getting {ticker} stock data: {str(e)}")
                retries += 1
                delay *= 2  # Exponential backoff
                if retries <= self.max_retries:
                    logger.warning(f"Retry {retries} getting {ticker} data, waiting {delay} seconds")
                else:
                    logger.error(f"Failed to get {ticker} data, maximum retries reached")
                    return None
        
        return None
        
    def generate_daily_report(self, ticker):
        """Generate daily analysis report"""
        try:
            # Get data
            hist = self.get_stock_data(ticker, '5d')
            if hist is None:
                return {"error": "Unable to get stock data"}
            
            # Calculate key metrics
            latest = hist.iloc[-1]
            prev_close = hist.iloc[-2]['Close']
            daily_change = (latest['Close'] - prev_close) / prev_close * 100
            
            # Volatility analysis
            atr = (hist['High'] - hist['Low']).mean()
            
            # Generate report
            report = {
                "date": datetime.today().strftime('%Y-%m-%d'),
                "price": latest['Close'],
                "change": daily_change,
                "volume": latest['Volume']/1e6,
                "atr": atr,
                "volume_alert": self.detect_abnormal_volume(hist),
                "technical_signals": self.generate_technical_signals(hist),
                "volatility_alert": self.volatility_cluster_alert(hist),
                "money_flow": self.money_flow_analysis(hist)
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating daily report for {ticker}: {str(e)}")
            return {"error": str(e)}

    def detect_abnormal_volume(self, data):
        """Volume anomaly detection"""
        avg_volume = data['Volume'].rolling(5).mean().iloc[-1]
        latest_volume = data['Volume'].iloc[-1]
        
        if latest_volume > avg_volume * 2:
            return "Volume breakout: Current volume is more than 2x the 5-day average"
        elif latest_volume < avg_volume * 0.5:
            return "Low trading: Current volume is less than half of 5-day average"
        else:
            return "Volume is within normal range"
        
    def generate_technical_signals(self, data):
        """Generate technical signals"""
        signals = []
        
        # Calculate MACD
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
            signals.append("MACD Golden Cross")
        elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
            signals.append("MACD Death Cross")
            
        # Calculate RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        if rsi.iloc[-1] > 70:
            signals.append(f"RSI Overbought ({rsi.iloc[-1]:.1f})")
        elif rsi.iloc[-1] < 30:
            signals.append(f"RSI Oversold ({rsi.iloc[-1]:.1f})")
            
        return signals

    def volatility_cluster_alert(self, data):
        """Volatility cluster analysis"""
        returns = data['Close'].pct_change().dropna()
        clusters = []
        threshold = returns.std() * 1.5
        
        for r in returns[-5:]:
            if abs(r) > threshold:
                clusters.append(1)
            else:
                clusters.append(0)
        
        if sum(clusters) >= 3:
            return "Volatility Cluster Warning: More than 3 abnormal fluctuations recently"
        return "Normal Volatility"

    def money_flow_analysis(self, data):
        """
        More sensitive money flow analysis, quick market response
        """
        try:
            # Calculate price change rate
            price_change = data['Close'].pct_change() * 100
            
            # Calculate volume change rate
            volume_change = data['Volume'].pct_change() * 100
            
            # Calculate typical price
            typical_price = (data['High'] + data['Low'] + data['Close']) / 3
            
            # Calculate Money Flow
            raw_money_flow = typical_price * data['Volume']
            
            # Use shorter-term money flow indicators
            positive_flow = raw_money_flow.where(typical_price > typical_price.shift(1), 0).rolling(window=10).sum()
            negative_flow = raw_money_flow.where(typical_price < typical_price.shift(1), 0).rolling(window=10).sum()
            
            # Calculate MFI (using shorter period)
            mfi = 100 - (100 / (1 + positive_flow / negative_flow))
            
            # Calculate OBV and short-term changes
            obv = (data['Volume'] * (~data['Close'].diff().le(0) * 2 - 1)).cumsum()
            obv_change = obv.diff(3) / obv.abs().mean() * 100  # Shortened to 3 days
            
            # Get latest values
            current_price_change = price_change.iloc[-1]
            current_volume_change = volume_change.iloc[-1]
            current_mfi = mfi.iloc[-1]
            current_obv_change = obv_change.iloc[-1]
            
            # More sensitive uptrend characteristics
            is_strong_uptrend = (
                current_price_change > 2 and  # Lowered to 2%
                current_volume_change > 30 and  # Lowered to 30%
                current_obv_change > 3  # Lowered to 3%
            )
            
            # More sensitive downtrend characteristics
            is_strong_downtrend = (
                current_price_change < -2 and  # Raised to -2%
                current_volume_change > 30 and  # Lowered to 30%
                current_obv_change < -3  # Raised to -3%
            )
            
            # Comprehensive analysis (more sensitive criteria)
            if is_strong_uptrend:
                if current_mfi > 70:  # Lower threshold
                    return "Strong capital inflow: Strong uptrend"
                else:
                    return "Accelerating capital inflow: Bullish signal"
            elif is_strong_downtrend:
                if current_mfi < 30:  # Higher threshold
                    return "Accelerating capital outflow: Bearish signal"
                else:
                    return "Continuous capital outflow: Risk warning"
            else:
                if current_mfi > 70 and current_obv_change < -3:
                    return "Capital outflow warning: Profit taking"
                elif current_mfi < 30 and current_obv_change > 3:
                    return "Capital inflow signal: Low-level accumulation"
                elif current_mfi > 55 and current_obv_change > 2:  # Lower threshold
                    return "Continuous capital inflow: Bulls dominate"
                elif current_mfi < 45 and current_obv_change < -2:  # Higher threshold
                    return "Gradual capital outflow: Bears dominate"
                elif current_price_change > 0.5 and current_volume_change > 10:  # More sensitive short-term judgment
                    return "Small capital inflow: Short-term bullish"
                elif current_price_change < -0.5 and current_volume_change > 10:
                    return "Small capital outflow: Short-term caution"
                else:
                    return "Capital flow neutral: Waiting for signals"
            
        except Exception as e:
            logger.error(f"Error in money flow analysis: {str(e)}")
            return "Money flow analysis error"

    def backtest_analysis(self, ticker: str, start_date: str, end_date: str):
        """Get analysis report for specified dates and verify accuracy"""
        try:
            logger.info(f"Attempting to fetch data for {ticker}")
            logger.info(f"Date range: {start_date} to {end_date}")

            # Convert dates to Pandas format
            start_date_pd = pd.to_datetime(start_date)
            end_date_pd = pd.to_datetime(end_date)

            # Get data for specified date range
            hist = self.get_stock_data(
                ticker, 
                start=start_date_pd - pd.Timedelta(days=7),  # Get 7 extra days for technical indicators
                end=end_date_pd + pd.Timedelta(days=5)      # Ensure end_date is included
            )
            
            if hist is None or hist.empty:
                logger.error(f"No data available for {ticker}")
                return {"error": "Unable to get historical data"}

            # Ensure index is datetime type
            hist.index = pd.to_datetime(hist.index)
            
            # Check if data range covers target dates
            if hist.index[0].date() > start_date_pd.date() or hist.index[-1].date() < end_date_pd.date():
                logger.error(f"Insufficient data range: {hist.index[0]} to {hist.index[-1]}")
                return {"error": "Data does not cover specified date range"}

            # Exact target date matching
            target_date = end_date_pd.date()
            matching_dates = hist.index[hist.index.date == target_date]
            
            if len(matching_dates) == 0:
                logger.error(f"Target date {end_date} not found in data")
                return {"error": f"No trading data for {end_date}"}

            target_idx = hist.index.get_loc(matching_dates[0])
            
            # Check for next trading day data
            if target_idx >= len(hist) - 1:
                logger.error(f"No next day data available for {ticker} at {end_date}")
                return {"error": f"Unable to get next trading day data for {end_date}"}

            # Record found dates
            test_date = hist.index[target_idx]
            next_date = hist.index[target_idx + 1]
            logger.info(f"Using test date: {test_date}")
            logger.info(f"Next trading day: {next_date}")

            # Generate analysis report using target date data
            test_data = hist.iloc[target_idx:target_idx+1]
            next_day = hist.iloc[target_idx+1]
            analysis_data = hist[:target_idx+1]

            # Generate report
            report = {
                "date": test_data.index[0].strftime('%Y-%m-%d'),
                "price": test_data['Close'].iloc[0],
                "change": ((test_data['Close'].iloc[0] - test_data['Open'].iloc[0]) / 
                        test_data['Open'].iloc[0] * 100),
                "volume": test_data['Volume'].iloc[0] / 1e6,  # Convert to millions
                "technical_signals": self.generate_technical_signals(analysis_data),
                "volatility_alert": self.volatility_cluster_alert(analysis_data),
                "money_flow": self.money_flow_analysis(analysis_data),
                "volume_alert": self.detect_abnormal_volume(analysis_data),
                "next_day": {
                    "date": next_day.name.strftime('%Y-%m-%d'),
                    "price": next_day['Close'],
                    "change": ((next_day['Close'] - next_day['Open']) / next_day['Open'] * 100)
                }
            }

            # Add next day data
            report["next_day"] = {
                "date": next_day.name.strftime('%Y-%m-%d'),
                "price": next_day['Close'],
                "change": ((next_day['Close'] - next_day['Open']) / next_day['Open'] * 100)
            }

            return report

        except Exception as e:
            logger.error(f"Unexpected error in backtest analysis for {ticker}: {str(e)}")
            return {"error": str(e)}