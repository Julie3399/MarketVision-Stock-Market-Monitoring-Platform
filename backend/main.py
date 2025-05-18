from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from services.stock_monitor import StockMonitor
from services.alert_service import AlertService
from services.stock_scanner import StockScanner
from services.stock_analyzer import StockAnalyzer
import logging
import sys
from pydantic import BaseModel
from typing import Optional, List, Dict
import yfinance as yf
import requests
import time
import json
import os
from pathlib import Path
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import urllib.parse
# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stock Monitor API", debug=True)

# Update CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Explicitly specify frontend domain
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handling
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )

# Initialize services
# stock_monitor = StockMonitor()
# alert_service = AlertService()
# stock_scanner = StockScanner()
stock_analyzer = StockAnalyzer()

# Create data directory
data_dir = Path(__file__).parent / 'data'
data_dir.mkdir(exist_ok=True)
watchlist_file = data_dir / 'watchlist.json'

# Initialize data
if not watchlist_file.exists():
    initial_data = {
        "Default Group": {
            "description": "Default Group",
            "stocks": ["NVDA", "TSLA", "MARA", "RIOT", "COIN"]
        },
        "Technology": {
            "description": "Technology Stocks",
            "stocks": ["NVDA", "TSLA"]
        },
        "Crypto Related": {
            "description": "Cryptocurrency Related Stocks",
            "stocks": ["MARA", "RIOT", "COIN"]
        }
    }
    watchlist_file.write_text(json.dumps(initial_data, ensure_ascii=False, indent=2))

def load_watchlist():
    """Load watchlist from file"""
    try:
        return json.loads(watchlist_file.read_text())
    except Exception as e:
        logger.error(f"Error loading watchlist: {str(e)}")
        return {}

def save_watchlist(data):
    """Save watchlist to file"""
    try:
        watchlist_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.error(f"Error saving watchlist: {str(e)}")
        raise

# Modify global variable
STOCK_GROUPS = load_watchlist()

class StockAdd(BaseModel):
    symbol: str
    group: Optional[str] = "Default Group"

@app.post("/api/watchlist/add")
async def add_to_watchlist(stock: StockAdd, request: Request):
    try:
        # Log received raw request data
        raw_data = await request.json()
        logger.info(f"Received raw request data: {raw_data}")
        logger.info(f"Parsed stock data: {stock}")
        logger.info(f"Adding stock {stock.symbol} to group {stock.group}")
        
        # Reload latest watchlist data before adding stock
        current_watchlist = load_watchlist()
        
        # Ensure group exists
        if stock.group not in current_watchlist:
            logger.info(f"Creating new group {stock.group}")
            current_watchlist[stock.group] = {
                "description": stock.group,
                "stocks": [],
                "subGroups": {}
            }
        
        # Check if stock already in group
        if stock.symbol not in current_watchlist[stock.group]["stocks"]:
            current_watchlist[stock.group]["stocks"].append(stock.symbol)
            logger.info(f"Added {stock.symbol} to {stock.group}")
            
            # Save changes
            save_watchlist(current_watchlist)
            
            # Update global variable
            global STOCK_GROUPS
            STOCK_GROUPS = current_watchlist.copy()  # Use copy to avoid reference issues
            
            return {
                "success": True,
                "message": f"Successfully added {stock.symbol} to {stock.group}",
                "groups": current_watchlist
            }
        else:
            logger.info(f"Stock {stock.symbol} already in group {stock.group}")
            return {
                "success": True,
                "message": f"Stock {stock.symbol} already exists in {stock.group}",
                "groups": current_watchlist
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding stock to watchlist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class StockGroup(BaseModel):
    name: str
    description: Optional[str] = None

class StockMove(BaseModel):
    symbol: str
    from_group: str
    to_group: str

class GroupMove(BaseModel):
    source_group: str
    target_group: str

class GroupRename(BaseModel):
    old_path: str
    new_name: str

class GroupReorder(BaseModel):
    source_group: str
    target_group: str
    position: str  # 'before' or 'after'

class StockReorder(BaseModel):
    group: str
    source_symbol: str
    target_symbol: str
    position: str  # 'before' or 'after'

# Add new Pydantic model for notes
class StockNote(BaseModel):
    symbol: str
    note: str

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up FastAPI application")

@app.get("/", status_code=200)
async def root():
    logger.info("Handling root endpoint request")
    try:
        response = {"message": "Welcome to Stock Monitor API"}
        logger.info(f"Returning response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in root endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/watchlist")
async def get_watchlist():
    logger.info("Fetching watchlist")
    try:
        # Reload from file every time watchlist is requested
        current_watchlist = load_watchlist()
        global STOCK_GROUPS
        STOCK_GROUPS = current_watchlist.copy()  # Update global variable
        return {"groups": STOCK_GROUPS}
    except Exception as e:
        logger.error(f"Error in get_watchlist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/alerts/{symbol}")
# async def check_alerts(symbol: str):
#     try:
#         alerts = stock_monitor.check_alerts(symbol)
#         return alerts
#     except Exception as e:
#         logger.error(f"Error checking alerts for {symbol}: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/scanner")
# async def scan_stocks():
#     try:
#         results = stock_scanner.scan_market()
#         return results
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/watchlist/{group:path}/{symbol}")
async def remove_stock(group: str, symbol: str):
    try:
        logger.info(f"Received group: {group}, symbol: {symbol}")
        
        # Load current watchlist
        watchlist = load_watchlist()
        
        # Handle nested group paths
        group_parts = group.split('/')
        current_group = watchlist
        
        # Traverse group path
        for i, part in enumerate(group_parts[:-1]):  # Except last part
            if part not in current_group:
                raise HTTPException(status_code=404, detail=f"Group {part} does not exist")
            if "subGroups" not in current_group[part]:
                current_group[part]["subGroups"] = {}
            current_group = current_group[part]["subGroups"]
        
        # Handle last group
        last_part = group_parts[-1]
        if last_part not in current_group:
            raise HTTPException(status_code=404, detail=f"Group {last_part} does not exist")
        
        if "stocks" not in current_group[last_part]:
            current_group[last_part]["stocks"] = []
        
        if symbol not in current_group[last_part]["stocks"]:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not in group {last_part}")
        
        # Remove stock from group
        current_group[last_part]["stocks"].remove(symbol)
        
        # Delete group if empty and not default group
        if (last_part != "Default Group" and 
            len(current_group[last_part]["stocks"]) == 0 and 
            (not current_group[last_part].get("subGroups") or 
             len(current_group[last_part]["subGroups"]) == 0)):
            del current_group[last_part]
        
        # Save changes
        save_watchlist(watchlist)
        
        return {
            "success": True,
            "message": f"Removed {symbol} from {group}",
            "groups": watchlist
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove stock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/groups")
async def add_group(group: StockGroup):
    try:
        if group.name in STOCK_GROUPS:
            raise HTTPException(status_code=400, detail="Group already exists")
        STOCK_GROUPS[group.name] = {"description": group.description, "stocks": []}
        # Save changes
        save_watchlist(STOCK_GROUPS)
        return {"status": "success", "message": f"Added group {group.name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/validate/{symbol}")
async def validate_stock(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1d')
        
        if hist.empty:
            return {"valid": False, "error": "Unable to fetch stock data"}
            
        info = ticker.info
        return {
            "valid": True,
            "name": info.get('longName', '') or info.get('shortName', ''),
            "price": hist['Close'][-1] if not hist.empty else 0
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}

@app.get("/api/stock/search/{query}")
async def search_stocks(query: str):
    try:
        # Add headers and delay
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Add retry mechanism
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                search_url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
                response = requests.get(search_url, headers=headers)
                
                if response.status_code == 429:  # Rate limit
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        return []  # Maximum retries reached
                
                response.raise_for_status()
                data = response.json()
                
                # Filter and format results
                suggestions = []
                for item in data.get('quotes', [])[:10]:
                    if item.get('quoteType') == 'EQUITY':
                        suggestions.append({
                            'symbol': item.get('symbol'),
                            'name': item.get('longname') or item.get('shortname'),
                            'exchange': item.get('exchange')
                        })
                return suggestions
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                logger.error(f"Request failed after {max_retries} attempts: {str(e)}")
                return []
                
    except Exception as e:
        logger.error(f"Error in stock search: {str(e)}")
        # Return empty list instead of raising error to prevent frontend crash
        return []

@app.get("/api/stock/analysis/{symbol}")
async def analyze_stock(symbol: str):
    """Get stock analysis report"""
    try:
        report = stock_analyzer.generate_daily_report(symbol)
        return report
    except Exception as e:
        logger.error(f"Error analyzing stock {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/backtest/{symbol}")
async def backtest_stock(symbol: str, start_date: str, end_date: str):
    """Get stock backtest analysis results"""
    try:
        logger.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")
        results = stock_analyzer.backtest_analysis(symbol, start_date, end_date)
        
        if isinstance(results, dict) and "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])
            
        logger.info(f"Backtest completed successfully")
        return results
    except Exception as e:
        logger.error(f"Error in backtest analysis for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist/move")
async def move_stock(move: StockMove):
    try:
        logger.info(f"Moving stock {move.symbol} from {move.from_group} to {move.to_group}")
        
        # Load current watchlist
        watchlist = load_watchlist()
        
        # Handle source group path
        from_parts = move.from_group.split('/')
        current_from = watchlist
        
        # Traverse source group path
        for i, part in enumerate(from_parts[:-1]):
            if part not in current_from:
                raise HTTPException(status_code=404, detail=f"Source group {part} does not exist")
            if "subGroups" not in current_from[part]:
                raise HTTPException(status_code=404, detail=f"Source group {part} has no subgroups")
            current_from = current_from[part]["subGroups"]
            
        # Check last source group
        last_from = from_parts[-1]
        if last_from not in current_from:
            raise HTTPException(status_code=404, detail=f"Source group {last_from} does not exist")
            
        # Check if stock is in source group
        if move.symbol not in current_from[last_from]["stocks"]:
            raise HTTPException(status_code=404, detail=f"Stock {move.symbol} not in group {last_from}")
            
        # Handle target group path
        to_parts = move.to_group.split('/')
        current_to = watchlist
        
        # Traverse target group path
        for i, part in enumerate(to_parts[:-1]):
            if part not in current_to:
                raise HTTPException(status_code=404, detail=f"Target group {part} does not exist")
            if "subGroups" not in current_to[part]:
                current_to[part]["subGroups"] = {}
            current_to = current_to[part]["subGroups"]
            
        # Check last target group
        last_to = to_parts[-1]
        if last_to not in current_to:
            raise HTTPException(status_code=404, detail=f"Target group {last_to} does not exist")
            
        # Ensure target group has stocks array
        if "stocks" not in current_to[last_to]:
            current_to[last_to]["stocks"] = []
            
        # Remove stock from source group
        current_from[last_from]["stocks"].remove(move.symbol)
        
        # Add to target group
        if move.symbol not in current_to[last_to]["stocks"]:
            current_to[last_to]["stocks"].append(move.symbol)
            
        # Delete source group if empty and not default group
        if (last_from != "Default Group" and 
            len(current_from[last_from]["stocks"]) == 0 and 
            (not current_from[last_from].get("subGroups") or 
             len(current_from[last_from]["subGroups"]) == 0)):
            del current_from[last_from]
            
        # Save changes
        save_watchlist(watchlist)
        
        return {
            "success": True,
            "message": f"Moved {move.symbol} from {move.from_group} to {move.to_group}",
            "groups": watchlist
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to move stock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/groups/move")
async def move_group(move: GroupMove):
    try:
        logger.info(f"Moving group {move.source_group} to {move.target_group}")
        
        # Load current watchlist
        watchlist = load_watchlist()
        
        # Check if source group exists
        if move.source_group not in watchlist:
            raise HTTPException(status_code=404, detail=f"Source group {move.source_group} does not exist")
            
        # Get group data to move
        moving_group = watchlist[move.source_group]
        
        # If target path is empty, move to top level
        if not move.target_group:
            # Add directly to top level
            watchlist[move.source_group] = moving_group
        else:
            # Check if target group exists
            if move.target_group not in watchlist:
                raise HTTPException(status_code=404, detail=f"Target group {move.target_group} does not exist")
                
            # Ensure target group has subGroups field
            if 'subGroups' not in watchlist[move.target_group]:
                watchlist[move.target_group]['subGroups'] = {}
                
            # Move group to target position
            watchlist[move.target_group]['subGroups'][move.source_group] = moving_group
            
            # Delete from original position
            del watchlist[move.source_group]
        
        # Save changes
        save_watchlist(watchlist)
        
        # Update global variable
        global STOCK_GROUPS
        STOCK_GROUPS = watchlist
        
        return {
            "status": "success",
            "message": f"Successfully moved group {move.source_group}",
            "groups": watchlist
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving group: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/groups/{group_path}")
async def delete_group(group_path: str):
    try:
        # Split path for nested cases
        path_parts = group_path.split('/')
        
        if path_parts[0] == "Default Group":
            raise HTTPException(status_code=400, detail="Cannot delete Default Group")
        
        # Recursively find group to delete
        current_groups = STOCK_GROUPS
        parent_groups = None
        target_group_name = None
        
        for i, part in enumerate(path_parts):
            if part not in current_groups:
                raise HTTPException(status_code=404, detail=f"Group {part} does not exist")
            
            if i == len(path_parts) - 1:  # Last part
                parent_groups = current_groups
                target_group_name = part
            else:
                current_groups = current_groups[part].get('subGroups', {})
        
        if not parent_groups or not target_group_name:
            raise HTTPException(status_code=404, detail="Target group not found")
            
        # Move stocks to Default Group
        group_to_delete = parent_groups[target_group_name]
        default_stocks = set(STOCK_GROUPS["Default Group"]["stocks"])
        
        # Recursively collect stocks from all subgroups
        def collect_stocks(group):
            stocks = set(group.get("stocks", []))
            for subgroup in group.get("subGroups", {}).values():
                stocks.update(collect_stocks(subgroup))
            return stocks
        
        all_stocks = collect_stocks(group_to_delete)
        STOCK_GROUPS["Default Group"]["stocks"] = list(default_stocks | all_stocks)
        
        # Delete group
        del parent_groups[target_group_name]
        
        # Save changes
        save_watchlist(STOCK_GROUPS)
        return {"status": "success", "message": f"Successfully deleted group {group_path}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting group: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/groups/rename")
async def rename_group(rename: GroupRename):
    try:
        # Decode path
        old_path = urllib.parse.unquote(rename.old_path)
        
        if old_path == "Default Group":
            raise HTTPException(status_code=400, detail="Cannot rename Default Group")
            
        # Find group to rename
        if old_path not in STOCK_GROUPS:
            raise HTTPException(status_code=404, detail=f"Group {old_path} does not exist")
            
        # Check if new name already exists
        if rename.new_name in STOCK_GROUPS:
            raise HTTPException(status_code=400, detail=f"Group name {rename.new_name} already exists")
            
        # Rename group
        STOCK_GROUPS[rename.new_name] = STOCK_GROUPS.pop(old_path)
        
        # Save changes
        save_watchlist(STOCK_GROUPS)
        return {"status": "success", "message": f"Successfully renamed group {old_path} to {rename.new_name}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renaming group: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/groups/reorder")
async def reorder_groups(reorder: GroupReorder):
    try:
        logger.info(f"Reordering group {reorder.source_group} {reorder.position} {reorder.target_group}")
        
        # Load current watchlist
        watchlist = load_watchlist()
        
        # Check if source and target groups exist
        if reorder.source_group not in watchlist:
            raise HTTPException(status_code=404, detail=f"Source group {reorder.source_group} does not exist")
        if reorder.target_group not in watchlist:
            raise HTTPException(status_code=404, detail=f"Target group {reorder.target_group} does not exist")
            
        # Get list of all groups
        groups = list(watchlist.keys())
        
        # Find positions of source and target groups
        source_index = groups.index(reorder.source_group)
        target_index = groups.index(reorder.target_group)
        
        # Remove source group from list
        groups.pop(source_index)
        
        # Reinsert source group based on position
        new_index = target_index if reorder.position == 'before' else target_index + 1
        groups.insert(new_index, reorder.source_group)
        
        # Create new ordered dictionary
        new_watchlist = {}
        for group in groups:
            new_watchlist[group] = watchlist[group]
            
        # Save changes
        save_watchlist(new_watchlist)
        
        # Update global variable
        global STOCK_GROUPS
        STOCK_GROUPS = new_watchlist
        
        return {
            "status": "success",
            "message": f"Successfully reordered group {reorder.source_group}",
            "groups": new_watchlist
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering groups: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist/reorder")
async def reorder_stocks(reorder: StockReorder):
    try:
        logger.info(f"Reordering stock {reorder.source_symbol} {reorder.position} {reorder.target_symbol} in group {reorder.group}")
        
        # Load current watchlist
        watchlist = load_watchlist()
        
        # Handle nested group paths
        group_parts = reorder.group.split('/')
        current_group = watchlist
        
        # Traverse group path
        for i, part in enumerate(group_parts[:-1]):  # Except last part
            if part not in current_group:
                raise HTTPException(status_code=404, detail=f"Group {part} does not exist")
            current_group = current_group[part]["subGroups"]
            
        # Check last group
        last_part = group_parts[-1]
        if last_part not in current_group:
            raise HTTPException(status_code=404, detail=f"Group {last_part} does not exist")
            
        group_data = current_group[last_part]
        
        # Check if source and target stocks exist
        if reorder.source_symbol not in group_data["stocks"]:
            raise HTTPException(status_code=404, detail=f"Stock {reorder.source_symbol} not in group")
        if reorder.target_symbol not in group_data["stocks"]:
            raise HTTPException(status_code=404, detail=f"Target stock {reorder.target_symbol} not in group")
            
        # Get stock list
        stocks = group_data["stocks"]
        
        # Remove source stock
        stocks.remove(reorder.source_symbol)
        
        # Get target position
        target_index = stocks.index(reorder.target_symbol)
        
        # Reinsert source stock based on position
        if reorder.position == 'after':
            target_index += 1
        stocks.insert(target_index, reorder.source_symbol)
        
        # Save changes
        save_watchlist(watchlist)
        
        return {
            "success": True,
            "message": f"Successfully reordered stock {reorder.source_symbol}",
            "groups": watchlist
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering stocks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/note/{symbol}")
async def get_stock_note(symbol: str):
    """Get stock note"""
    try:
        # Load note data from file
        notes_file = data_dir / 'stock_notes.json'
        if not notes_file.exists():
            return {"note": ""}
            
        with open(notes_file, 'r', encoding='utf-8') as f:
            notes = json.load(f)
            
        return {"note": notes.get(symbol, "")}
    except Exception as e:
        logger.error(f"Error getting note for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stock/note")
async def update_stock_note(note: StockNote):
    """Update stock note"""
    try:
        notes_file = data_dir / 'stock_notes.json'
        
        # Load existing notes
        if notes_file.exists():
            with open(notes_file, 'r', encoding='utf-8') as f:
                notes = json.load(f)
        else:
            notes = {}
            
        # Update note
        notes[note.symbol] = note.note
        
        # Save updated notes
        with open(notes_file, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": "Note updated successfully"}
    except Exception as e:
        logger.error(f"Error updating note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))