import requests
import pandas as pd
from datetime import datetime
import time

class BinanceAPI:
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        })
    
    def _make_request(self, endpoint, params=None, retries=3):
        """
        Make HTTP request with retry logic
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    print(f"API request failed after {retries} attempts: {str(e)}")
                    return None
    
    def get_klines(self, symbol, interval, limit=200):
        """
        Fetch candlestick data from Binance
        
        Parameters:
        - symbol: Trading pair (e.g., 'BTCUSDT')
        - interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        - limit: Number of candles to fetch (max 1000)
        
        Returns pandas DataFrame with OHLCV data
        """
        endpoint = "/api/v3/klines"
        
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': min(limit, 1000)
        }
        
        data = self._make_request(endpoint, params)
        
        if not data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # Convert data types
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # Keep only necessary columns
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        return df
    
    def get_current_price(self, symbol):
        """
        Get current price for a symbol
        """
        endpoint = "/api/v3/ticker/price"
        
        params = {'symbol': symbol.upper()}
        
        data = self._make_request(endpoint, params)
        
        if data and 'price' in data:
            return float(data['price'])
        return None
    
    def get_24h_ticker(self, symbol):
        """
        Get 24-hour ticker statistics
        """
        endpoint = "/api/v3/ticker/24hr"
        
        params = {'symbol': symbol.upper()}
        
        data = self._make_request(endpoint, params)
        
        if not data:
            return None
        
        return {
            'symbol': data.get('symbol'),
            'price_change': float(data.get('priceChange', 0)),
            'price_change_percent': float(data.get('priceChangePercent', 0)),
            'last_price': float(data.get('lastPrice', 0)),
            'high_price': float(data.get('highPrice', 0)),
            'low_price': float(data.get('lowPrice', 0)),
            'volume': float(data.get('volume', 0)),
            'quote_volume': float(data.get('quoteVolume', 0)),
            'open_time': datetime.fromtimestamp(int(data.get('openTime', 0)) / 1000),
            'close_time': datetime.fromtimestamp(int(data.get('closeTime', 0)) / 1000)
        }
    
    def get_exchange_info(self, symbol=None):
        """
        Get exchange information for a symbol or all symbols
        """
        endpoint = "/api/v3/exchangeInfo"
        
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        data = self._make_request(endpoint, params)
        
        return data
    
    def get_orderbook(self, symbol, limit=100):
        """
        Get order book depth
        """
        endpoint = "/api/v3/depth"
        
        params = {
            'symbol': symbol.upper(),
            'limit': min(limit, 5000)
        }
        
        data = self._make_request(endpoint, params)
        
        if not data:
            return None
        
        return {
            'bids': [[float(price), float(qty)] for price, qty in data.get('bids', [])],
            'asks': [[float(price), float(qty)] for price, qty in data.get('asks', [])],
            'last_update_id': data.get('lastUpdateId')
        }
    
    def get_recent_trades(self, symbol, limit=100):
        """
        Get recent trades
        """
        endpoint = "/api/v3/trades"
        
        params = {
            'symbol': symbol.upper(),
            'limit': min(limit, 1000)
        }
        
        data = self._make_request(endpoint, params)
        
        if not data:
            return None
        
        trades = []
        for trade in data:
            trades.append({
                'id': trade.get('id'),
                'price': float(trade.get('price', 0)),
                'qty': float(trade.get('qty', 0)),
                'time': datetime.fromtimestamp(int(trade.get('time', 0)) / 1000),
                'is_buyer_maker': trade.get('isBuyerMaker', False)
            })
        
        return trades
    
    def validate_symbol(self, symbol):
        """
        Validate if symbol exists on Binance
        """
        info = self.get_exchange_info(symbol)
        
        if info and 'symbols' in info:
            return len(info['symbols']) > 0
        return False
    
    def get_available_intervals(self):
        """
        Get list of available timeframe intervals
        """
        return [
            '1m', '3m', '5m', '15m', '30m',
            '1h', '2h', '4h', '6h', '8h', '12h',
            '1d', '3d', '1w', '1M'
        ]
    
    def convert_interval_to_minutes(self, interval):
        """
        Convert interval string to minutes
        """
        interval_map = {
            '1m': 1,
            '3m': 3,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '2h': 120,
            '4h': 240,
            '6h': 360,
            '8h': 480,
            '12h': 720,
            '1d': 1440,
            '3d': 4320,
            '1w': 10080,
            '1M': 43200
        }
        
        return interval_map.get(interval, 0)
    
    def calculate_candles_needed(self, interval, days):
        """
        Calculate how many candles are needed for X days
        """
        minutes_per_day = 1440
        interval_minutes = self.convert_interval_to_minutes(interval)
        
        if interval_minutes == 0:
            return 0
        
        total_minutes = days * minutes_per_day
        return int(total_minutes / interval_minutes)
    
    def get_server_time(self):
        """
        Get Binance server time
        """
        endpoint = "/api/v3/time"
        
        data = self._make_request(endpoint)
        
        if data and 'serverTime' in data:
            return datetime.fromtimestamp(int(data['serverTime']) / 1000)
        return None
    
    def ping(self):
        """
        Test connectivity to Binance API
        """
        endpoint = "/api/v3/ping"
        
        data = self._make_request(endpoint)
        
        return data is not None
