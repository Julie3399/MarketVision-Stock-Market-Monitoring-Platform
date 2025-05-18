import requests
import logging
import time
import random
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("user_agent_test.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("user_agent_tester")

# List of user agents to test
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "curl/7.68.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0"
]

# Test stock tickers
test_tickers = ["AAPL", "MSFT", "XIACY"]

# API endpoints to test
api_endpoints = [
    "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
    "https://query2.finance.yahoo.com/v8/finance/chart/{ticker}",
    "https://query1.finance.yahoo.com/v7/finance/chart/{ticker}",
    "https://query2.finance.yahoo.com/v7/finance/chart/{ticker}"
]

def test_user_agent(user_agent, ticker, endpoint_template):
    """Test a single user agent"""
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://finance.yahoo.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Upgrade-Insecure-Requests": "1"
    }
    
    url = endpoint_template.format(ticker=ticker)
    params = {
        "interval": "1d",
        "includePrePost": True,
        "events": "div,splits,capitalGains",
        "range": "5d"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        status_code = response.status_code
        
        if status_code == 200:
            logger.info(f"Success: {user_agent} - {ticker} - {url} - Status Code: {status_code}")
            return True
        else:
            logger.warning(f"Failed: {user_agent} - {ticker} - {url} - Status Code: {status_code}")
            return False
    except Exception as e:
        logger.error(f"Error: {user_agent} - {ticker} - {url} - Exception: {str(e)}")
        return False

def main():
    """Main test function"""
    results = {}
    
    # Create results dictionary for each user agent
    for agent in user_agents:
        results[agent] = {"success": 0, "fail": 0, "success_tickers": [], "fail_tickers": []}
    
    # Test each user agent
    for agent in user_agents:
        logger.info(f"Testing user agent: {agent}")
        
        for ticker in test_tickers:
            # Randomly select an API endpoint
            endpoint = random.choice(api_endpoints)
            
            # Add random delay to avoid rate limiting
            delay = 2 + random.uniform(1, 3)
            logger.info(f"Waiting {delay:.2f} seconds before requesting {ticker} data")
            time.sleep(delay)
            
            # Test the user agent
            success = test_user_agent(agent, ticker, endpoint)
            
            if success:
                results[agent]["success"] += 1
                results[agent]["success_tickers"].append(ticker)
            else:
                results[agent]["fail"] += 1
                results[agent]["fail_tickers"].append(ticker)
    
    # Output results summary
    logger.info("\n===== Test Results Summary =====")
    for agent, result in results.items():
        success_rate = result["success"] / (result["success"] + result["fail"]) * 100 if (result["success"] + result["fail"]) > 0 else 0
        logger.info(f"User Agent: {agent}")
        logger.info(f"Success Rate: {success_rate:.2f}% ({result['success']}/{result['success'] + result['fail']})")
        logger.info(f"Successful Tickers: {', '.join(result['success_tickers'])}")
        logger.info(f"Failed Tickers: {', '.join(result['fail_tickers'])}")
        logger.info("------------------------")
    
    # Find the best user agent
    best_agent = max(results.items(), key=lambda x: x[1]["success"])
    logger.info(f"Best User Agent: {best_agent[0]} (Success Rate: {best_agent[1]['success'] / (best_agent[1]['success'] + best_agent[1]['fail']) * 100:.2f}%)")

if __name__ == "__main__":
    main()