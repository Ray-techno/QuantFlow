import re
import json
from datetime import datetime, timedelta
import pandas as pd

def format_price(price, decimals=2):
    """
    Format price with proper decimal places and thousand separators
    """
    if price is None:
        return "N/A"
    
    try:
        price = float(price)
        return f"${price:,.{decimals}f}"
    except (ValueError, TypeError):
        return "N/A"

def format_percentage(value, decimals=2):
    """
    Format percentage value
    """
    if value is None:
        return "N/A"
    
    try:
        value = float(value)
        sign = "+" if value >= 0 else ""
        return f"{sign}{value:.{decimals}f}%"
    except (ValueError, TypeError):
        return "N/A"

def format_volume(volume):
    """
    Format volume with K, M, B suffixes
    """
    if volume is None:
        return "N/A"
    
    try:
        volume = float(volume)
        
        if volume >= 1_000_000_000:
            return f"{volume / 1_000_000_000:.2f}B"
        elif volume >= 1_000_000:
            return f"{volume / 1_000_000:.2f}M"
        elif volume >= 1_000:
            return f"{volume / 1_000:.2f}K"
        else:
            return f"{volume:.2f}"
    except (ValueError, TypeError):
        return "N/A"

def validate_webhook_url(url):
    """
    Validate Discord webhook URL
    """
    if not url:
        return False, "URL is empty"
    
    pattern = r'^https://discord\.com/api/webhooks/\d+/[\w-]+$'
    
    if re.match(pattern, url):
        return True, "Valid webhook URL"
    else:
        return False, "Invalid Discord webhook URL format"

def validate_symbol(symbol):
    """
    Validate trading symbol format
    """
    if not symbol:
        return False, "Symbol is empty"
    
    # Basic validation: alphanumeric, 4-20 characters
    if re.match(r'^[A-Z0-9]{4,20}$', symbol.upper()):
        return True, "Valid symbol"
    else:
        return False, "Invalid symbol format (use uppercase letters and numbers)"

def calculate_price_change(old_price, new_price):
    """
    Calculate price change percentage
    """
    if not old_price or old_price == 0:
        return 0
    
    try:
        old_price = float(old_price)
        new_price = float(new_price)
        change = ((new_price - old_price) / old_price) * 100
        return round(change, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

def calculate_risk_reward_ratio(entry, stop_loss, take_profit):
    """
    Calculate risk/reward ratio
    """
    try:
        entry = float(entry)
        stop_loss = float(stop_loss)
        take_profit = float(take_profit)
        
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        
        if risk == 0:
            return 0
        
        return round(reward / risk, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

def calculate_position_size(account_balance, risk_percentage, entry_price, stop_loss_price):
    """
    Calculate position size based on risk management
    """
    try:
        account_balance = float(account_balance)
        risk_percentage = float(risk_percentage)
        entry_price = float(entry_price)
        stop_loss_price = float(stop_loss_price)
        
        risk_amount = account_balance * (risk_percentage / 100)
        price_difference = abs(entry_price - stop_loss_price)
        
        if price_difference == 0:
            return 0
        
        position_size = risk_amount / price_difference
        return round(position_size, 8)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

def timeframe_to_seconds(timeframe):
    """
    Convert timeframe string to seconds
    """
    timeframe_map = {
        '1m': 60,
        '3m': 180,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '2h': 7200,
        '4h': 14400,
        '6h': 21600,
        '8h': 28800,
        '12h': 43200,
        '1d': 86400,
        '3d': 259200,
        '1w': 604800
    }
    
    return timeframe_map.get(timeframe.lower(), 0)

def get_next_candle_close_time(current_time, timeframe):
    """
    Calculate when the next candle will close
    """
    seconds = timeframe_to_seconds(timeframe)
    
    if seconds == 0:
        return None
    
    current_timestamp = int(current_time.timestamp())
    next_close = ((current_timestamp // seconds) + 1) * seconds
    
    return datetime.fromtimestamp(next_close)

def format_time_remaining(target_time):
    """
    Format time remaining until target time
    """
    if not target_time:
        return "N/A"
    
    now = datetime.now()
    
    if target_time <= now:
        return "Closed"
    
    delta = target_time - now
    
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    seconds = delta.seconds % 60
    
    if delta.days > 0:
        return f"{delta.days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def export_to_json(data, filename):
    """
    Export data to JSON file
    """
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4, default=str)
        return True, f"Data exported to {filename}"
    except Exception as e:
        return False, f"Export failed: {str(e)}"

def import_from_json(filename):
    """
    Import data from JSON file
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return True, data
    except FileNotFoundError:
        return False, "File not found"
    except json.JSONDecodeError:
        return False, "Invalid JSON format"
    except Exception as e:
        return False, f"Import failed: {str(e)}"

def export_to_csv(dataframe, filename):
    """
    Export pandas DataFrame to CSV
    """
    try:
        dataframe.to_csv(filename, index=False)
        return True, f"Data exported to {filename}"
    except Exception as e:
        return False, f"Export failed: {str(e)}"

def sanitize_filename(filename):
    """
    Sanitize filename by removing invalid characters
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    max_length = 200
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:max_length - len(ext) - 1] + '.' + ext if ext else name[:max_length]
    
    return filename

def generate_signal_id():
    """
    Generate unique signal ID
    """
    return f"SIG_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

def parse_timeframe_input(user_input):
    """
    Parse user-friendly timeframe input
    """
    timeframe_mapping = {
        '1 minute': '1m',
        '5 minutes': '5m',
        '15 minutes': '15m',
        '30 minutes': '30m',
        '1 hour': '1h',
        '4 hours': '4h',
        '1 day': '1d',
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '1h': '1h',
        '4h': '4h',
        '1d': '1d'
    }
    
    return timeframe_mapping.get(user_input.lower(), None)

def calculate_candle_body_percentage(open_price, close_price, high, low):
    """
    Calculate percentage of candle body vs total range
    """
    try:
        total_range = high - low
        body_size = abs(close_price - open_price)
        
        if total_range == 0:
            return 0
        
        return round((body_size / total_range) * 100, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

def is_bullish_candle(open_price, close_price):
    """
    Check if candle is bullish
    """
    try:
        return float(close_price) > float(open_price)
    except (ValueError, TypeError):
        return False

def is_bearish_candle(open_price, close_price):
    """
    Check if candle is bearish
    """
    try:
        return float(close_price) < float(open_price)
    except (ValueError, TypeError):
        return False

def calculate_average(values):
    """
    Calculate average of a list of values
    """
    if not values:
        return 0
    
    try:
        numeric_values = [float(v) for v in values if v is not None]
        if not numeric_values:
            return 0
        return sum(numeric_values) / len(numeric_values)
    except (ValueError, TypeError):
        return 0

def get_timeframe_display_name(timeframe):
    """
    Get user-friendly timeframe display name
    """
    display_names = {
        '1m': '1 Minute',
        '3m': '3 Minutes',
        '5m': '5 Minutes',
        '15m': '15 Minutes',
        '30m': '30 Minutes',
        '1h': '1 Hour',
        '2h': '2 Hours',
        '4h': '4 Hours',
        '6h': '6 Hours',
        '8h': '8 Hours',
        '12h': '12 Hours',
        '1d': '1 Day',
        '3d': '3 Days',
        '1w': '1 Week',
        '1M': '1 Month'
    }
    
    return display_names.get(timeframe, timeframe)

def truncate_string(text, max_length=50):
    """
    Truncate string to max length with ellipsis
    """
    if not text:
        return ""
    
    text = str(text)
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."

def format_timestamp(timestamp, format_string="%Y-%m-%d %H:%M:%S"):
    """
    Format timestamp to readable string
    """
    try:
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return timestamp.strftime(format_string)
    except Exception:
        return str(timestamp)
