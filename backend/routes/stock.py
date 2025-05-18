from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
import json
import os

stock_bp = Blueprint('stock', __name__)

# Load local stock data
def load_stock_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, '..', 'data', 'us_stocks.json')
        with open(data_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading stock data: {str(e)}")
        return {}

# Load watchlist data
def load_watchlist():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        watchlist_path = os.path.join(current_dir, '..', 'data', 'watchlist.json')
        with open(watchlist_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading watchlist: {str(e)}")
        return {"Default Group": {"description": "Default Group", "stocks": []}}

# Save watchlist data
def save_watchlist(watchlist):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        watchlist_path = os.path.join(current_dir, '..', 'data', 'watchlist.json')
        with open(watchlist_path, 'w') as f:
            json.dump(watchlist, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving watchlist: {str(e)}")
        return False

# Global variable to store stock data
STOCK_DATABASE = load_stock_data()

@stock_bp.route('/watchlist/add', methods=['POST'])
@cross_origin(supports_credentials=True)
def add_to_watchlist():
    try:
        data = request.get_json()
        print(f"Received add stock request: {data}")
        
        symbol = data.get('symbol')
        group = data.get('group', 'Default Group')
        
        if not symbol:
            print("Error: Stock symbol is empty")
            return jsonify({"error": "Stock symbol cannot be empty"}), 400

        # Verify if stock exists in local database
        print(f"Verifying if stock {symbol} exists in database")
        print(f"Stocks in database: {list(STOCK_DATABASE.keys())}")
        
        if symbol not in STOCK_DATABASE:
            print(f"Error: Stock {symbol} not in database")
            return jsonify({"error": "Invalid stock symbol"}), 400
            
        # Load current watchlist
        print("Loading watchlist")
        watchlist = load_watchlist()
        print(f"Current watchlist: {watchlist}")
        
        # Ensure group exists
        if group not in watchlist:
            print(f"Creating new group: {group}")
            watchlist[group] = {
                "description": group,
                "stocks": [],
                "subGroups": {}
            }
        
        # Check if stock is already in watchlist
        if symbol not in watchlist[group]["stocks"]:
            print(f"Adding stock {symbol} to group {group}")
            watchlist[group]["stocks"].append(symbol)
            
            # Save updated watchlist
            if save_watchlist(watchlist):
                print("Watchlist saved successfully")
                return jsonify({
                    "success": True,
                    "message": f"Successfully added {symbol} to {group}",
                    "groups": watchlist
                })
            else:
                print("Error: Failed to save watchlist")
                return jsonify({"error": "Failed to save watchlist"}), 500
        else:
            print(f"Stock {symbol} already in watchlist")
            return jsonify({
                "success": True,
                "message": f"Stock {symbol} is already in watchlist",
                "groups": watchlist
            })
            
    except Exception as e:
        print(f"Error adding stock: {str(e)}")
        return jsonify({"error": str(e)}), 500

@stock_bp.route('/stock/search/<query>', methods=['GET'])
@cross_origin(supports_credentials=True)
def search_stock(query):
    try:
        print(f"Received search query: {query}")
        
        # Filter matching stocks
        results = []
        query = query.upper().strip()
        
        # Try exact match first
        if query in STOCK_DATABASE:
            info = STOCK_DATABASE[query]
            results.append({
                "ticker": query,
                "name": info['name'],
                "exchange": info['exchange']
            })
            return jsonify(results)
        
        # If no exact match, try partial matches
        for ticker, info in STOCK_DATABASE.items():
            # Match ticker
            if query in ticker:
                results.append({
                    "ticker": ticker,
                    "name": info['name'],
                    "exchange": info['exchange']
                })
                continue
            
            # Match company name (case insensitive)
            if query.lower() in info['name'].lower():
                results.append({
                    "ticker": ticker,
                    "name": info['name'],
                    "exchange": info['exchange']
                })
        
        # Sort by ticker length, prioritize shorter tickers
        results.sort(key=lambda x: len(x['ticker']))
        
        # Limit number of results
        results = results[:10]
        
        print(f"Returning results: {results}")
        return jsonify(results)
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@stock_bp.route('/delete', methods=['DELETE'])
@cross_origin(supports_credentials=True)
def delete_stock():
    try:
        group = request.args.get('group')
        symbol = request.args.get('symbol')
        
        if not group or not symbol:
            return jsonify({"error": "Group and stock symbol cannot be empty"}), 400
            
        # Load current watchlist
        watchlist = load_watchlist()
        
        # Handle nested group paths
        group_parts = group.split('/')
        current_group = watchlist
        
        # Traverse group path
        for i, part in enumerate(group_parts):
            if part not in current_group:
                return jsonify({"error": f"Group {part} does not exist"}), 404
                
            if i == len(group_parts) - 1:  # Last group
                if symbol not in current_group[part]["stocks"]:
                    return jsonify({"error": f"Stock {symbol} not in group {part}"}), 404
                    
                # Remove stock from group
                current_group[part]["stocks"].remove(symbol)
                
                # If group is empty and not default group, delete it
                if (part != "Default Group" and 
                    len(current_group[part]["stocks"]) == 0 and 
                    (not current_group[part].get("subGroups") or len(current_group[part]["subGroups"]) == 0)):
                    del current_group[part]
            else:
                current_group = current_group[part]["subGroups"]
        
        # Save changes
        if save_watchlist(watchlist):
            return jsonify({
                "success": True,
                "message": f"Successfully removed {symbol} from {group}",
                "groups": watchlist
            })
        else:
            return jsonify({"error": "Failed to save watchlist"}), 500
            
    except Exception as e:
        print(f"Error deleting stock: {str(e)}")
        return jsonify({"error": str(e)}), 500
