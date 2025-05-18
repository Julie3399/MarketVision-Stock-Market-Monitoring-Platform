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
        # 设置Chrome选项
        self.options = Options()
        self.options.add_argument("--headless")  # 无头模式，不显示浏览器
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        
        # 添加更真实的用户代理
        self.options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        # 初始化浏览器实例
        self.driver = None
        
    def _initialize_driver(self):
        """初始化WebDriver"""
        if self.driver is None:
            logger.info("初始化Chrome WebDriver...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.options)
            
    def _close_driver(self):
        """关闭WebDriver"""
        if self.driver is not None:
            logger.info("关闭Chrome WebDriver...")
            self.driver.quit()
            self.driver = None
            
    def get_stock_data(self, ticker, period='1y', interval='1d'):
        """
        通过Google代理获取Yahoo Finance股票数据
        
        参数:
            ticker (str): 股票代码，例如 "AAPL" 或 "9992.HK"
            period (str): 时间段，例如 "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"
            interval (str): 时间间隔，例如 "1m", "2m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo"
            
        返回:
            pandas.DataFrame: 包含股票数据的DataFrame
        """
        try:
            self._initialize_driver()
            
            # 构建Yahoo Finance API URL
            yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range={period}"
            
            # 通过Google搜索该URL
            google_url = f"https://www.google.com/search?q={yahoo_url}"
            logger.info(f"通过Google访问: {google_url}")
            
            # 访问Google搜索页面
            self.driver.get(google_url)
            time.sleep(2)  # 等待页面加载
            
            # 查找搜索结果中的第一个链接（通常是Yahoo Finance API的直接链接）
            search_results = self.driver.find_elements(By.CSS_SELECTOR, "div.g a")
            
            if not search_results:
                logger.warning("未找到搜索结果链接")
                # 尝试直接在Google中打开Yahoo Finance URL
                logger.info(f"直接在Google中打开Yahoo Finance URL")
                self.driver.get(yahoo_url)
                time.sleep(3)  # 等待页面加载
                
                # 获取页面内容
                page_source = self.driver.page_source
                
                # 提取JSON数据
                if "chart" in page_source:
                    # 页面内容可能是JSON或包含JSON的HTML
                    start_marker = '{"chart":'
                    end_marker = '}'
                    
                    start_idx = page_source.find(start_marker)
                    if start_idx != -1:
                        # 找到JSON开始位置
                        json_str = page_source[start_idx:]
                        
                        # 计算嵌套的大括号来找到正确的结束位置
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
                                logger.error(f"JSON解析错误: {e}")
                    else:
                        logger.error("页面中未找到JSON数据")
            else:
                # 点击第一个搜索结果
                first_link = search_results[0]
                first_link.click()
                time.sleep(3)  # 等待页面加载
                
                # 获取页面内容
                page_source = self.driver.page_source
                
                # 提取JSON数据
                try:
                    # 假设页面内容是纯JSON
                    data = json.loads(page_source)
                    return self._parse_yahoo_data(data)
                except json.JSONDecodeError:
                    # 如果不是纯JSON，尝试从页面中提取JSON
                    if "chart" in page_source:
                        start_marker = '{"chart":'
                        start_idx = page_source.find(start_marker)
                        if start_idx != -1:
                            # 找到JSON开始位置
                            json_str = page_source[start_idx:]
                            
                            # 计算嵌套的大括号来找到正确的结束位置
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
                                    logger.error(f"JSON解析错误: {e}")
            
            logger.error("无法获取股票数据")
            return None
            
        except Exception as e:
            logger.error(f"获取股票数据时发生错误: {str(e)}")
            return None
        finally:
            self._close_driver()
    
    def _parse_yahoo_data(self, data):
        """解析Yahoo Finance返回的JSON数据"""
        try:
            chart_data = data['chart']['result'][0]
            timestamps = chart_data['timestamp']
            quote = chart_data['indicators']['quote'][0]
            
            # 创建DataFrame
            df = pd.DataFrame({
                'Open': quote.get('open', []),
                'High': quote.get('high', []),
                'Low': quote.get('low', []),
                'Close': quote.get('close', []),
                'Volume': quote.get('volume', [])
            }, index=pd.to_datetime(timestamps, unit='s'))
            
            # 处理调整后的收盘价
            if 'adjclose' in chart_data['indicators']:
                df['Adj Close'] = chart_data['indicators']['adjclose'][0]['adjclose']
            
            # 清理数据：移除NaN和重复索引
            df = df.dropna().loc[~df.index.duplicated(keep='first')]
            
            return df
            
        except (KeyError, IndexError) as e:
            logger.error(f"解析数据失败: {str(e)}")
            return None