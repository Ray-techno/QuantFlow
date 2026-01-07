import pandas as pd
import numpy as np
from datetime import datetime
import json

class IndicatorEngine:
    """Engine for executing and managing indicators"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.builtin_indicators = self._load_builtin_indicators()
    
    def _load_builtin_indicators(self):
        """Load built-in indicator library"""
        return {
            'sma': {
                'name': 'Simple Moving Average',
                'category': 'Trend',
                'params': {'period': 20},
                'code': '''def calculate(df, period=20):
    """Simple Moving Average"""
    return df['close'].rolling(window=period).mean()'''
            },
            'ema': {
                'name': 'Exponential Moving Average',
                'category': 'Trend',
                'params': {'period': 20},
                'code': '''def calculate(df, period=20):
    """Exponential Moving Average"""
    return df['close'].ewm(span=period, adjust=False).mean()'''
            },
            'rsi': {
                'name': 'Relative Strength Index',
                'category': 'Momentum',
                'params': {'period': 14},
                'code': '''def calculate(df, period=14):
    """RSI Indicator"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi'''
            },
            'macd': {
                'name': 'MACD',
                'category': 'Momentum',
                'params': {'fast': 12, 'slow': 26, 'signal': 9},
                'code': '''def calculate(df, fast=12, slow=26, signal=9):
    """MACD Indicator"""
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    })'''
            },
            'bb': {
                'name': 'Bollinger Bands',
                'category': 'Volatility',
                'params': {'period': 20, 'std': 2},
                'code': '''def calculate(df, period=20, std=2):
    """Bollinger Bands"""
    sma = df['close'].rolling(window=period).mean()
    std_dev = df['close'].rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return pd.DataFrame({
        'upper': upper,
        'middle': sma,
        'lower': lower
    })'''
            },
            'atr': {
                'name': 'Average True Range',
                'category': 'Volatility',
                'params': {'period': 14},
                'code': '''def calculate(df, period=14):
    """ATR Indicator"""
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr'''
            },
            'stoch': {
                'name': 'Stochastic Oscillator',
                'category': 'Momentum',
                'params': {'k_period': 14, 'd_period': 3},
                'code': '''def calculate(df, k_period=14, d_period=3):
    """Stochastic Oscillator"""
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    k = 100 * (df['close'] - low_min) / (high_max - low_min)
    d = k.rolling(window=d_period).mean()
    return pd.DataFrame({'k': k, 'd': d})'''
            },
            'adx': {
                'name': 'Average Directional Index',
                'category': 'Trend',
                'params': {'period': 14},
                'code': '''def calculate(df, period=14):
    """ADX Indicator"""
    high_diff = df['high'].diff()
    low_diff = -df['low'].diff()
    
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    
    tr_list = [df['high'] - df['low'],
               abs(df['high'] - df['close'].shift()),
               abs(df['low'] - df['close'].shift())]
    tr = pd.concat(tr_list, axis=1).max(axis=1)
    
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return pd.DataFrame({'adx': adx, 'plus_di': plus_di, 'minus_di': minus_di})'''
            },
            'vwap': {
                'name': 'Volume Weighted Average Price',
                'category': 'Volume',
                'params': {},
                'code': '''def calculate(df):
    """VWAP Indicator"""
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    return vwap'''
            },
            'obv': {
                'name': 'On Balance Volume',
                'category': 'Volume',
                'params': {},
                'code': '''def calculate(df):
    """OBV Indicator"""
    obv = (df['volume'] * (~df['close'].diff().le(0) * 2 - 1)).cumsum()
    return obv'''
            }
        }
    
    def execute_indicator(self, code, df, params=None):
        """
        Safely execute indicator code
        
        Returns: pd.Series or pd.DataFrame with indicator values
        """
        try:
            # Create safe namespace
            namespace = {
                'pd': pd,
                'np': np,
                'df': df.copy(),
                '__builtins__': {
                    'abs': abs,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'len': len,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'round': round,
                    'float': float,
                    'int': int,
                    'str': str,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'True': True,
                    'False': False,
                    'None': None
                }
            }
            
            # Execute code
            exec(code, namespace)
            
            # Call calculate function
            if 'calculate' in namespace:
                if params:
                    result = namespace['calculate'](df, **params)
                else:
                    result = namespace['calculate'](df)
                return result
            else:
                raise Exception("Code must define a 'calculate' function")
                
        except Exception as e:
            raise Exception(f"Indicator execution error: {str(e)}")
    
    def check_alert_conditions(self, indicator_data, alert_config):
        """
        Check if indicator alert conditions are met
        
        alert_config = {
            'type': 'crossover' | 'value' | 'compare',
            'condition': 'above' | 'below' | 'crosses_above' | 'crosses_below' | 'equals',
            'value': threshold_value,
            'compare_with': 'signal_line' | other_series
        }
        """
        if indicator_data is None or indicator_data.empty:
            return False, None
        
        alert_type = alert_config.get('type', 'value')
        condition = alert_config.get('condition', 'above')
        threshold = alert_config.get('value', 0)
        
        # Get last two values (current and previous)
        if isinstance(indicator_data, pd.DataFrame):
            # Multi-line indicator (e.g., MACD)
            main_line = alert_config.get('line', list(indicator_data.columns)[0])
            current = indicator_data[main_line].iloc[-1]
            previous = indicator_data[main_line].iloc[-2] if len(indicator_data) > 1 else None
        else:
            # Single line indicator
            current = indicator_data.iloc[-1]
            previous = indicator_data.iloc[-2] if len(indicator_data) > 1 else None
        
        # Check conditions
        if alert_type == 'value':
            if condition == 'above':
                return current > threshold, {'current': current, 'threshold': threshold}
            elif condition == 'below':
                return current < threshold, {'current': current, 'threshold': threshold}
            elif condition == 'equals':
                return abs(current - threshold) < 0.01, {'current': current, 'threshold': threshold}
        
        elif alert_type == 'crossover' and previous is not None:
            if condition == 'crosses_above':
                crossed = previous <= threshold < current
                return crossed, {'current': current, 'previous': previous, 'threshold': threshold}
            elif condition == 'crosses_below':
                crossed = previous >= threshold > current
                return crossed, {'current': current, 'previous': previous, 'threshold': threshold}
        
        elif alert_type == 'compare' and isinstance(indicator_data, pd.DataFrame):
            compare_line = alert_config.get('compare_with')
            if compare_line and compare_line in indicator_data.columns:
                compare_current = indicator_data[compare_line].iloc[-1]
                compare_previous = indicator_data[compare_line].iloc[-2] if len(indicator_data) > 1 else None
                
                if condition == 'crosses_above' and compare_previous is not None:
                    crossed = previous <= compare_previous and current > compare_current
                    return crossed, {
                        'main_current': current,
                        'compare_current': compare_current
                    }
                elif condition == 'crosses_below' and compare_previous is not None:
                    crossed = previous >= compare_previous and current < compare_current
                    return crossed, {
                        'main_current': current,
                        'compare_current': compare_current
                    }
        
        return False, None
    
    def get_indicator_library(self):
        """Get all available indicators"""
        builtin = [
            {
                'id': key,
                'name': val['name'],
                'category': val['category'],
                'params': val['params'],
                'type': 'builtin'
            }
            for key, val in self.builtin_indicators.items()
        ]
        
        # Add custom indicators from database
        custom = self.db.get_custom_indicators()
        
        return {
            'builtin': builtin,
            'custom': custom
        }
    
    def get_indicator_code(self, indicator_id):
        """Get indicator code by ID"""
        if indicator_id in self.builtin_indicators:
            return self.builtin_indicators[indicator_id]['code']
        else:
            # Get from database
            return self.db.get_indicator_code(indicator_id)
    
    def format_indicator_for_chart(self, indicator_data, indicator_config):
        """
        Format indicator data for chart display
        
        Returns dict with plot configuration
        """
        plot_config = {
            'type': indicator_config.get('plot_type', 'line'),
            'color': indicator_config.get('color', '#2962FF'),
            'width': indicator_config.get('width', 2),
            'overlay': indicator_config.get('overlay', True),
            'data': {}
        }
        
        if isinstance(indicator_data, pd.DataFrame):
            # Multi-line indicator
            for col in indicator_data.columns:
                plot_config['data'][col] = indicator_data[col].tolist()
        else:
            # Single line
            plot_config['data']['main'] = indicator_data.tolist()
        
        return plot_config
