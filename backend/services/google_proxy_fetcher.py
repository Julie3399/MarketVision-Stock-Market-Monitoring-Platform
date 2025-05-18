import json
import logging
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

logger = logging.getLogger(__name__)

class GoogleProxyFetcher:
    def __init__(self):
        # Set Chrome options
        self.options = Options()
        self.options.add_argument("--headless")  # Headless mode, browser not displayed
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        
        # Add more realistic user agent
        self.options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        # Initialize browser instance
        self.driver = None
        
    def _initialize_driver(self):
        """Initialize WebDriver"""
        if self.driver is None:
            logger.info("Initializing Chrome WebDriver...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.options)
            
    def _close_driver(self):
        """Close WebDriver"""
        if self.driver is not None:
            logger.info("Closing Chrome WebDriver...")
            self.driver.quit()
            self.driver = None
            
    def get_stock_data(self, ticker, period='1y', interval='1d'):
        """
        Get Yahoo Finance stock data through Google proxy
        
        Parameters:
            ticker (str): Stock code, e.g. "AAPL" or "9992.HK"
            period (str): Time period, e.g. "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"
            interval (str): Time interval, e.g. "1m", "2m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo"
            
        Returns:
            pandas.DataFrame: DataFrame containing stock data
        """
        try:
            self._initialize_driver()
            
            # Build Yahoo Finance API URL
            yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range={period}"
            
            # Search for URL through Google
            google_url = f"https://www.google.com/search?q={yahoo_url}"
            logger.info(f"Accessing through Google: {google_url}")
            
            # Visit Google search page
            self.driver.get(google_url)
            time.sleep(2)  # Wait for page to load
            
            # Find first link in search results (usually direct link to Yahoo Finance API)
            search_results = self.driver.find_elements(By.CSS_SELECTOR, "div.g a")
            
            if not search_results:
                logger.warning("No search result links found")
                # Try opening Yahoo Finance URL directly in Google
                logger.info(f"Opening Yahoo Finance URL directly in Google")
                self.driver.get(yahoo_url)
                time.sleep(3)  # Wait for page to load
                
                # Get page content
                page_source = self.driver.page_source
                
                # Extract JSON data
                if "chart" in page_source:
                    # Page content might be JSON or HTML containing JSON
                    start_marker = '{"chart":'
                    end_marker = '}'
                    
                    start_idx = page_source.find(start_marker)
                    if start_idx != -1:
                        # Found JSON start position
                        json_str = page_source[start_idx:]
                        
                        # Calculate nested braces to find correct end position
                        brace_count = 0
                        end_idx = 0
                        
                        for i, char in enumerate(json_str):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        if end_idx > 0:
                            json_data = json_str[:end_idx]
                            try:
                                data = json.loads(json_data)
                                return self._parse_yahoo_data(data)
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON parsing error: {e}")
                    else:
                        logger.error("No JSON data found in page")
            else:
                # Click first search result
                first_link = search_results[0]
                first_link.click()
                time.sleep(3)  # Wait for page to load
                
                # Get page content
                page_source = self.driver.page_source
                
                # Extract JSON data
                try:
                    # Assume page content is pure JSON
                    data = json.loads(page_source)
                    return self._parse_yahoo_data(data)
                except json.JSONDecodeError:
                    # If not pure JSON, try extracting JSON from page
                    if "chart" in page_source:
                        start_marker = '{"chart":'
                        start_idx = page_source.find(start_marker)
                        if start_idx != -1:
                            # Found JSON start position
                            json_str = page_source[start_idx:]
                            
                            # Calculate nested braces to find correct end position
                            brace_count = 0
                            end_idx = 0
                            
                            for i, char in enumerate(json_str):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end_idx = i + 1
                                        break
                            
                            if end_idx > 0:
                                json_data = json_str[:end_idx]
                                try:
                                    data = json.loads(json_data)
                                    return self._parse_yahoo_data(data)
                                except json.JSONDecodeError as e:
                                    logger.error(f"JSON parsing error: {e}")
            
            logger.error("Unable to get stock data")
            return None
            
        except Exception as e:
            logger.error(f"Error occurred while getting stock data: {str(e)}")
            return None
        finally:
            self._close_driver()
    
    def _parse_yahoo_data(self, data):
        """Parse JSON data returned from Yahoo Finance"""
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
            
            return df
            
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse data: {str(e)}")
            return None