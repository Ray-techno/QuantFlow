import sqlite3
from datetime import datetime
from cryptography.fernet import Fernet
import os
import json

class DatabaseManager:
    def __init__(self, db_path='trading_platform.db'):
        self.db_path = db_path
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
        self.init_db()
        self.migrate_database()
    
    def _get_or_create_key(self):
        key_file = 'encryption.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def migrate_database(self):
        """Add new columns and tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check existing tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            # Add fvg_timeframe to user_settings if not exists
            if 'user_settings' in existing_tables:
                cursor.execute("PRAGMA table_info(user_settings)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'fvg_timeframe' not in columns:
                    cursor.execute("ALTER TABLE user_settings ADD COLUMN fvg_timeframe TEXT DEFAULT '5m'")
                    conn.commit()
            
            # Add timeframe columns to signals_history if not exists
            if 'signals_history' in existing_tables:
                cursor.execute("PRAGMA table_info(signals_history)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'price_timeframe' not in columns:
                    cursor.execute("ALTER TABLE signals_history ADD COLUMN price_timeframe TEXT")
                if 'fvg_timeframe' not in columns:
                    cursor.execute("ALTER TABLE signals_history ADD COLUMN fvg_timeframe TEXT")
                conn.commit()
            
            # Create indicators table if not exists
            if 'custom_indicators' not in existing_tables:
                cursor.execute('''
                CREATE TABLE custom_indicators (
                    indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    code TEXT NOT NULL,
                    category TEXT DEFAULT 'Custom',
                    params TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                ''')
                conn.commit()
                print("✅ Created custom_indicators table")
            
            # Create indicator_alerts table if not exists
            if 'indicator_alerts' not in existing_tables:
                cursor.execute('''
                CREATE TABLE indicator_alerts (
                    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    indicator_id INTEGER,
                    indicator_name TEXT,
                    alert_type TEXT,
                    condition TEXT,
                    value REAL,
                    webhook_url TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    last_triggered TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                ''')
                conn.commit()
                print("✅ Created indicator_alerts table")
            
            # Create applied_indicators table
            if 'applied_indicators' not in existing_tables:
                cursor.execute('''
                CREATE TABLE applied_indicators (
                    applied_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    indicator_id TEXT,
                    indicator_type TEXT,
                    params TEXT,
                    config TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                ''')
                conn.commit()
                print("✅ Created applied_indicators table")
                
        except Exception as e:
            print(f"❌ Migration error: {e}")
        finally:
            conn.close()
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_levels (
            level_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            price REAL NOT NULL,
            label TEXT,
            color TEXT DEFAULT '#2962FF',
            enabled BOOLEAN DEFAULT 1,
            triggered BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            symbol TEXT DEFAULT 'BTCUSDT',
            timeframe TEXT DEFAULT '15m',
            fvg_timeframe TEXT DEFAULT '5m',
            webhook_url TEXT,
            refresh_interval INTEGER DEFAULT 5,
            theme TEXT DEFAULT 'dark',
            notifications_enabled BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals_history (
            signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            symbol TEXT,
            timeframe TEXT,
            price_timeframe TEXT,
            fvg_timeframe TEXT,
            price_level REAL,
            trigger_price REAL,
            fvg_type TEXT,
            fvg_low REAL,
            fvg_high REAL,
            notified BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlists (
            watchlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT NOT NULL,
            enabled BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    # User management (existing methods)
    def create_user(self, username, email, password_hash):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                          (username, email, password_hash))
            user_id = cursor.lastrowid
            cursor.execute('INSERT INTO user_settings (user_id) VALUES (?)', (user_id,))
            conn.commit()
            conn.close()
            return True, user_id
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                return False, "Username exists"
            elif 'email' in str(e):
                return False, "Email exists"
            return False, "Registration failed"
    
    def get_user_by_username(self, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def update_last_login(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = ? WHERE user_id = ?',
                      (datetime.now(), user_id))
        conn.commit()
        conn.close()
    
    # Settings management (existing methods)
    def get_user_settings(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
        settings = cursor.fetchone()
        conn.close()
        return dict(settings) if settings else {
            'symbol': 'BTCUSDT', 'timeframe': '15m',
            'fvg_timeframe': '5m', 'refresh_interval': 5
        }
    
    def save_user_settings(self, user_id, settings):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE user_settings 
        SET symbol = ?, timeframe = ?, fvg_timeframe = ?, refresh_interval = ?
        WHERE user_id = ?
        ''', (settings.get('symbol'), settings.get('timeframe'),
              settings.get('fvg_timeframe', '5m'),
              settings.get('refresh_interval'), user_id))
        conn.commit()
        conn.close()
    
    def encrypt_webhook(self, webhook_url, user_id):
        encrypted = self.cipher.encrypt(webhook_url.encode()).decode()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE user_settings SET webhook_url = ? WHERE user_id = ?',
                      (encrypted, user_id))
        conn.commit()
        conn.close()
    
    def decrypt_webhook(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT webhook_url FROM user_settings WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result and result['webhook_url']:
            try:
                return self.cipher.decrypt(result['webhook_url'].encode()).decode()
            except:
                return None
        return None
    
    # Price levels (existing methods)
    def save_price_level(self, user_id, level_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO price_levels (user_id, price, label, color, enabled, triggered)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, level_data['price'], level_data['label'], level_data['color'],
              level_data['enabled'], level_data['triggered']))
        level_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return level_id
    
    def get_price_levels(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM price_levels WHERE user_id = ? ORDER BY created_at DESC',
                      (user_id,))
        levels = cursor.fetchall()
        conn.close()
        return [dict(level) for level in levels]
    
    def delete_price_level(self, level_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM price_levels WHERE level_id = ? AND user_id = ?',
                      (level_id, user_id))
        conn.commit()
        conn.close()
    
    def update_price_level_triggered(self, level_id, triggered=True):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE price_levels SET triggered = ? WHERE level_id = ?',
                      (triggered, level_id))
        conn.commit()
        conn.close()
    
    # Signals (existing methods)
    def save_signal(self, user_id, signal_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO signals_history 
        (user_id, symbol, timeframe, price_timeframe, fvg_timeframe, price_level,
         trigger_price, fvg_type, fvg_low, fvg_high, notified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, signal_data['symbol'],
              signal_data.get('timeframe', signal_data.get('price_timeframe', '')),
              signal_data.get('price_timeframe', ''),
              signal_data.get('fvg_timeframe', ''),
              signal_data['price_level'], signal_data['trigger_price'],
              signal_data['fvg_type'], signal_data['fvg_low'],
              signal_data['fvg_high'], signal_data.get('notified', False)))
        signal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return signal_id
    
    def get_signal_history(self, user_id, limit=100):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM signals_history 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
        ''', (user_id, limit))
        signals = cursor.fetchall()
        conn.close()
        return [dict(signal) for signal in signals]
    
    def get_user_signal_count(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM signals_history WHERE user_id = ?',
                      (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result['count'] if result else 0
    
    # NEW: Custom Indicators Management
    def save_custom_indicator(self, user_id, indicator_data):
        """Save custom indicator"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO custom_indicators (user_id, name, code, category, params)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, indicator_data['name'], indicator_data['code'],
              indicator_data.get('category', 'Custom'),
              json.dumps(indicator_data.get('params', {}))))
        indicator_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return indicator_id
    
    def get_custom_indicators(self, user_id=None):
        """Get all custom indicators for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if user_id:
            cursor.execute('SELECT * FROM custom_indicators WHERE user_id = ?', (user_id,))
        else:
            cursor.execute('SELECT * FROM custom_indicators')
        indicators = cursor.fetchall()
        conn.close()
        return [dict(ind) for ind in indicators]
    
    def get_indicator_code(self, indicator_id):
        """Get indicator code by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT code FROM custom_indicators WHERE indicator_id = ?',
                      (indicator_id,))
        result = cursor.fetchone()
        conn.close()
        return result['code'] if result else None
    
    def update_custom_indicator(self, indicator_id, indicator_data):
        """Update custom indicator"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE custom_indicators 
        SET name = ?, code = ?, category = ?, params = ?, updated_at = ?
        WHERE indicator_id = ?
        ''', (indicator_data['name'], indicator_data['code'],
              indicator_data.get('category', 'Custom'),
              json.dumps(indicator_data.get('params', {})),
              datetime.now(), indicator_id))
        conn.commit()
        conn.close()
    
    def delete_custom_indicator(self, indicator_id, user_id):
        """Delete custom indicator"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM custom_indicators WHERE indicator_id = ? AND user_id = ?',
                      (indicator_id, user_id))
        conn.commit()
        conn.close()
    
    # NEW: Indicator Alerts Management
    def save_indicator_alert(self, user_id, alert_data):
        """Save indicator alert"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO indicator_alerts 
        (user_id, indicator_id, indicator_name, alert_type, condition, value, webhook_url, enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, alert_data.get('indicator_id'), alert_data['indicator_name'],
              alert_data['alert_type'], alert_data['condition'],
              alert_data.get('value', 0), alert_data.get('webhook_url'),
              alert_data.get('enabled', True)))
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return alert_id
    
    def get_indicator_alerts(self, user_id):
        """Get all indicator alerts for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM indicator_alerts WHERE user_id = ? AND enabled = 1',
                      (user_id,))
        alerts = cursor.fetchall()
        conn.close()
        return [dict(alert) for alert in alerts]
    
    def update_alert_triggered(self, alert_id):
        """Update last triggered timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE indicator_alerts SET last_triggered = ? WHERE alert_id = ?',
                      (datetime.now(), alert_id))
        conn.commit()
        conn.close()
    
    def delete_indicator_alert(self, alert_id, user_id):
        """Delete indicator alert"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM indicator_alerts WHERE alert_id = ? AND user_id = ?',
                      (alert_id, user_id))
        conn.commit()
        conn.close()
    
    # NEW: Applied Indicators Management
    def save_applied_indicator(self, user_id, applied_data):
        """Save applied indicator to chart"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO applied_indicators 
        (user_id, indicator_id, indicator_type, params, config, enabled)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, applied_data['indicator_id'], applied_data['indicator_type'],
              json.dumps(applied_data.get('params', {})),
              json.dumps(applied_data.get('config', {})),
              applied_data.get('enabled', True)))
        applied_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return applied_id
    
    def get_applied_indicators(self, user_id):
        """Get all applied indicators for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applied_indicators WHERE user_id = ? AND enabled = 1',
                      (user_id,))
        applied = cursor.fetchall()
        conn.close()
        result = []
        for item in applied:
            d = dict(item)
            d['params'] = json.loads(d['params']) if d['params'] else {}
            d['config'] = json.loads(d['config']) if d['config'] else {}
            result.append(d)
        return result
    
    def delete_applied_indicator(self, applied_id, user_id):
        """Remove indicator from chart"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM applied_indicators WHERE applied_id = ? AND user_id = ?',
                      (applied_id, user_id))
        conn.commit()
        conn.close()
