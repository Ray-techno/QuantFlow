import pandas as pd
import numpy as np
from datetime import datetime

class TradingEngine:
    def __init__(self, db_manager, notification_manager):
        self.db = db_manager
        self.notifier = notification_manager
        self.triggered_levels = {}
    
    def detect_fvg(self, df, fvg_type_filter=None, start_idx=0):
        """
        Detect Fair Value Gaps, optionally filtering by type
        
        IMPORTANT: Excludes last candle (live/incomplete candle)
        
        Parameters:
        - df: DataFrame with candles
        - fvg_type_filter: 'Bullish', 'Bearish', or None (both)
        - start_idx: Start detecting from this index
        """
        fvg_list = []
        
        if len(df) < 4:  # Need at least 4 candles (excluding last live one)
            return fvg_list
        
        # IMPORTANT: Exclude last candle (it's still forming)
        # Only check completed candles
        df_completed = df.iloc[:-1].copy()
        
        if len(df_completed) < 3:
            return fvg_list
        
        start = max(2, start_idx)
        
        for i in range(start, len(df_completed)):
            # Bullish FVG Detection
            if df_completed.iloc[i-2]['high'] < df_completed.iloc[i]['low']:
                if fvg_type_filter is None or fvg_type_filter == 'Bullish':
                    fvg = {
                        'type': 'Bullish',
                        'index': i,
                        'timestamp': df_completed.iloc[i]['timestamp'],
                        'fvg_low': df_completed.iloc[i-2]['high'],
                        'fvg_high': df_completed.iloc[i]['low'],
                        'gap_size': df_completed.iloc[i]['low'] - df_completed.iloc[i-2]['high'],
                        'candle_1': df_completed.iloc[i-2].to_dict(),
                        'candle_2': df_completed.iloc[i-1].to_dict(),
                        'candle_3': df_completed.iloc[i].to_dict()
                    }
                    fvg_list.append(fvg)
            
            # Bearish FVG Detection
            elif df_completed.iloc[i-2]['low'] > df_completed.iloc[i]['high']:
                if fvg_type_filter is None or fvg_type_filter == 'Bearish':
                    fvg = {
                        'type': 'Bearish',
                        'index': i,
                        'timestamp': df_completed.iloc[i]['timestamp'],
                        'fvg_low': df_completed.iloc[i]['high'],
                        'fvg_high': df_completed.iloc[i-2]['low'],
                        'gap_size': df_completed.iloc[i-2]['low'] - df_completed.iloc[i]['high'],
                        'candle_1': df_completed.iloc[i-2].to_dict(),
                        'candle_2': df_completed.iloc[i-1].to_dict(),
                        'candle_3': df_completed.iloc[i].to_dict()
                    }
                    fvg_list.append(fvg)
        
        return fvg_list
    
    def get_current_price(self, df):
        """Get current price from last completed candle"""
        if df.empty or len(df) < 2:
            return None
        # Use second-to-last candle (last completed candle)
        return df.iloc[-2]['close']
    
    def determine_fvg_type(self, price_level, current_price):
        """
        Auto-determine expected FVG type based on price level position
        
        Logic:
        - Price level ABOVE current price → Expect BEARISH FVG (resistance, reversal down)
        - Price level BELOW current price → Expect BULLISH FVG (support, reversal up)
        - Price level AT current price → Check BOTH types
        """
        if price_level > current_price * 1.001:  # 0.1% above
            return 'Bearish'
        elif price_level < current_price * 0.999:  # 0.1% below
            return 'Bullish'
        else:
            return None  # Too close, check both
    
    def check_price_tap(self, df, price_levels, current_price):
        """
        Check if price tapped levels (excluding live candle)
        Also stores expected FVG type for each level
        """
        triggered_levels = []
        
        if df.empty or not price_levels:
            return triggered_levels
        
        # Exclude last candle (live candle)
        df_completed = df.iloc[:-1].copy() if len(df) > 1 else df.copy()
        
        for level in price_levels:
            if not level['enabled'] or level['triggered']:
                continue
            
            price = level['price']
            level_id = level['level_id']
            
            if level_id in self.triggered_levels:
                continue
            
            # Determine expected FVG type based on position
            expected_fvg_type = self.determine_fvg_type(price, current_price)
            
            # Check if any COMPLETED candle touched this price
            for idx, row in df_completed.iterrows():
                if row['low'] <= price <= row['high']:
                    triggered_info = {
                        'level': level,
                        'candle_index': idx,
                        'timestamp': row['timestamp'],
                        'candle_open': row['open'],
                        'candle_close': row['close'],
                        'candle_high': row['high'],
                        'candle_low': row['low'],
                        'expected_fvg_type': expected_fvg_type
                    }
                    triggered_levels.append(triggered_info)
                    
                    self.triggered_levels[level_id] = {
                        'tap_index': idx,
                        'tap_timestamp': row['timestamp'],
                        'tap_price': price,
                        'expected_fvg_type': expected_fvg_type
                    }
                    break
        
        return triggered_levels
    
    def check_fvg_after_tap(self, fvg_df, tap_timestamp, expected_fvg_type):
        """
        Check if NEW FVG formed AFTER tap, with correct type
        
        Parameters:
        - fvg_df: DataFrame for FVG detection
        - tap_timestamp: When price tapped
        - expected_fvg_type: 'Bullish', 'Bearish', or None (both)
        """
        if fvg_df.empty:
            return None
        
        # Find candles AFTER tap (excluding last live candle)
        post_tap_df = fvg_df[fvg_df['timestamp'] > tap_timestamp].reset_index(drop=True)
        
        if len(post_tap_df) < 4:  # Need 3 + 1 (to exclude last)
            return None
        
        # Detect FVG with type filter
        fvg_list = self.detect_fvg(post_tap_df, fvg_type_filter=expected_fvg_type, start_idx=2)
        
        if not fvg_list:
            return None
        
        return fvg_list[0]
    
    def check_fvg_signals(self, price_df, fvg_df, price_levels, user_id, symbol, price_timeframe, fvg_timeframe):
        """
        Main signal detection with smart FVG type selection
        
        Logic:
        1. Get current price from completed candles
        2. Determine expected FVG type for each level
        3. Check price taps on completed candles only
        4. Look for correct FVG type AFTER tap
        5. Trigger signal only when all conditions met
        """
        signals = []
        
        if price_df.empty or fvg_df.empty or not price_levels:
            return signals
        
        # Get current price from last COMPLETED candle
        current_price = self.get_current_price(price_df)
        if current_price is None:
            return signals
        
        # Check newly tapped levels
        newly_tapped = self.check_price_tap(price_df, price_levels, current_price)
        
        for tapped in newly_tapped:
            level = tapped['level']
            tap_timestamp = tapped['timestamp']
            expected_fvg_type = tapped['expected_fvg_type']
            
            # Look for FVG of correct type AFTER tap
            fvg = self.check_fvg_after_tap(fvg_df, tap_timestamp, expected_fvg_type)
            
            if fvg:
                # SIGNAL TRIGGERED!
                signal_data = {
                    'symbol': symbol,
                    'price_timeframe': price_timeframe,
                    'fvg_timeframe': fvg_timeframe,
                    'price_level': level['price'],
                    'trigger_price': tapped['candle_close'],
                    'tap_timestamp': tap_timestamp,
                    'fvg_type': fvg['type'],
                    'fvg_timestamp': fvg['timestamp'],
                    'fvg_low': fvg['fvg_low'],
                    'fvg_high': fvg['fvg_high'],
                    'gap_size': fvg['gap_size'],
                    'expected_type': expected_fvg_type or 'Any',
                    'notified': False
                }
                
                signal_id = self.db.save_signal(user_id, signal_data)
                signal_data['signal_id'] = signal_id
                
                self.db.update_price_level_triggered(level['level_id'], True)
                
                webhook_url = self.db.decrypt_webhook(user_id)
                if webhook_url:
                    self.notifier.send_discord_notification(webhook_url, signal_data, user_id)
                    signal_data['notified'] = True
                
                signals.append(signal_data)
        
        # Check previously tapped levels
        for level in price_levels:
            level_id = level['level_id']
            
            if level['triggered']:
                continue
            
            if level_id in self.triggered_levels:
                tap_info = self.triggered_levels[level_id]
                tap_timestamp = tap_info['tap_timestamp']
                expected_fvg_type = tap_info.get('expected_fvg_type')
                
                fvg = self.check_fvg_after_tap(fvg_df, tap_timestamp, expected_fvg_type)
                
                if fvg:
                    signal_data = {
                        'symbol': symbol,
                        'price_timeframe': price_timeframe,
                        'fvg_timeframe': fvg_timeframe,
                        'price_level': level['price'],
                        'trigger_price': tap_info['tap_price'],
                        'tap_timestamp': tap_timestamp,
                        'fvg_type': fvg['type'],
                        'fvg_timestamp': fvg['timestamp'],
                        'fvg_low': fvg['fvg_low'],
                        'fvg_high': fvg['fvg_high'],
                        'gap_size': fvg['gap_size'],
                        'expected_type': expected_fvg_type or 'Any',
                        'notified': False
                    }
                    
                    signal_id = self.db.save_signal(user_id, signal_data)
                    signal_data['signal_id'] = signal_id
                    
                    self.db.update_price_level_triggered(level['level_id'], True)
                    
                    webhook_url = self.db.decrypt_webhook(user_id)
                    if webhook_url:
                        self.notifier.send_discord_notification(webhook_url, signal_data, user_id)
                        signal_data['notified'] = True
                    
                    signals.append(signal_data)
                    del self.triggered_levels[level_id]
        
        return signals
    
    def calculate_support_resistance(self, df, window=20):
        """Calculate support and resistance levels"""
        levels = []
        
        if len(df) < window + 1:
            return levels
        
        # Exclude last candle
        df_completed = df.iloc[:-1].copy()
        
        for i in range(window, len(df_completed) - window):
            if df_completed.iloc[i]['high'] == df_completed.iloc[i-window:i+window+1]['high'].max():
                levels.append({
                    'type': 'resistance',
                    'price': df_completed.iloc[i]['high'],
                    'timestamp': df_completed.iloc[i]['timestamp']
                })
            
            if df_completed.iloc[i]['low'] == df_completed.iloc[i-window:i+window+1]['low'].min():
                levels.append({
                    'type': 'support',
                    'price': df_completed.iloc[i]['low'],
                    'timestamp': df_completed.iloc[i]['timestamp']
                })
        
        return levels
    
    def get_trading_recommendation(self, fvg_type, current_price, fvg_low, fvg_high):
        """Generate trading recommendations"""
        recommendation = {
            'action': '',
            'entry': 0,
            'stop_loss': 0,
            'take_profit': 0,
            'risk_reward': 0
        }
        
        if fvg_type == 'Bullish':
            recommendation['action'] = 'BUY'
            recommendation['entry'] = fvg_low
            recommendation['stop_loss'] = fvg_low - (fvg_high - fvg_low) * 0.5
            recommendation['take_profit'] = fvg_high + (fvg_high - fvg_low) * 2
        elif fvg_type == 'Bearish':
            recommendation['action'] = 'SELL'
            recommendation['entry'] = fvg_high
            recommendation['stop_loss'] = fvg_high + (fvg_high - fvg_low) * 0.5
            recommendation['take_profit'] = fvg_low - (fvg_high - fvg_low) * 2
        
        risk = abs(recommendation['entry'] - recommendation['stop_loss'])
        reward = abs(recommendation['take_profit'] - recommendation['entry'])
        
        if risk > 0:
            recommendation['risk_reward'] = round(reward / risk, 2)
        
        return recommendation
