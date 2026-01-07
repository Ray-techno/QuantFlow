import os
from datetime import timedelta

# Application Settings
APP_NAME = "FVG Trading Platform"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Trading Team"

# Database Settings
DATABASE_PATH = os.getenv('DATABASE_PATH', 'trading_platform.db')
ENCRYPTION_KEY_FILE = 'encryption.key'

# Binance API Settings
BINANCE_BASE_URL = "https://api.binance.com"
BINANCE_TESTNET_URL = "https://testnet.binance.vision"
USE_TESTNET = False  # Set to True for testing

# API Rate Limiting
API_REQUESTS_PER_MINUTE = 1200
API_REQUESTS_PER_SECOND = 20
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 2  # seconds
API_TIMEOUT = 10  # seconds

# Trading Settings
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_TIMEFRAME = "15m"
DEFAULT_CANDLE_LIMIT = 200
MAX_CANDLE_LIMIT = 1000

# Available Timeframes
AVAILABLE_TIMEFRAMES = [
    '1m', '3m', '5m', '15m', '30m',
    '1h', '2h', '4h', '6h', '8h', '12h',
    '1d', '3d', '1w', '1M'
]

# Supported Trading Pairs
POPULAR_SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT',
    'XRPUSDT', 'DOTUSDT', 'UNIUSDT', 'LINKUSDT', 'LTCUSDT',
    'SOLUSDT', 'MATICUSDT', 'AVAXUSDT', 'ATOMUSDT', 'XLMUSDT'
]

# FVG Detection Settings
FVG_MIN_GAP_SIZE = 0.0001  # Minimum gap size to consider as FVG
FVG_LOOKBACK_CANDLES = 5  # Number of candles to look back for FVG confirmation
FVG_QUALITY_THRESHOLD = 50  # Minimum quality score (0-100)

# Price Level Settings
MAX_PRICE_LEVELS_PER_USER = 50
DEFAULT_PRICE_LEVEL_COLOR = "#2962FF"
PRICE_LEVEL_COLORS = [
    "#2962FF",  # Blue
    "#26A69A",  # Green
    "#EF5350",  # Red
    "#FFA726",  # Orange
    "#AB47BC",  # Purple
    "#42A5F5",  # Light Blue
    "#66BB6A",  # Light Green
    "#FFEE58",  # Yellow
]

# Notification Settings
DISCORD_WEBHOOK_TIMEOUT = 10  # seconds
ENABLE_DISCORD_NOTIFICATIONS = True
ENABLE_EMAIL_NOTIFICATIONS = False  # Future feature
ENABLE_TELEGRAM_NOTIFICATIONS = False  # Future feature

# Notification Throttling
MAX_NOTIFICATIONS_PER_HOUR = 50
NOTIFICATION_COOLDOWN = 60  # seconds between same signal notifications

# Session Settings
SESSION_TIMEOUT = timedelta(hours=1)
REMEMBER_ME_DURATION = timedelta(days=30)
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION = timedelta(minutes=15)

# Password Requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL_CHARS = True

# User Settings
MAX_WATCHLIST_SYMBOLS = 20
MAX_SIGNAL_HISTORY = 1000
DEFAULT_REFRESH_INTERVAL = 5  # seconds
MIN_REFRESH_INTERVAL = 5  # seconds
MAX_REFRESH_INTERVAL = 60  # seconds

# UI Theme Settings
THEME_DARK = {
    'background': '#131722',
    'chart_background': '#1E222D',
    'grid_lines': '#363A45',
    'text': '#D1D4DC',
    'bullish_candle': '#26A69A',
    'bearish_candle': '#EF5350',
    'price_line': '#2962FF',
}

THEME_LIGHT = {
    'background': '#FFFFFF',
    'chart_background': '#F5F5F5',
    'grid_lines': '#E0E0E0',
    'text': '#000000',
    'bullish_candle': '#089981',
    'bearish_candle': '#F23645',
    'price_line': '#2962FF',
}

# Chart Settings
CHART_HEIGHT = 600
CHART_WIDTH = 1200
CHART_SHOW_VOLUME = True
CHART_SHOW_GRID = True
CHART_SHOW_CROSSHAIR = True

# Risk Management
DEFAULT_RISK_PERCENTAGE = 1.0  # % of account balance
MAX_RISK_PERCENTAGE = 5.0
DEFAULT_RISK_REWARD_RATIO = 2.0

# Data Export Settings
EXPORT_DATE_FORMAT = "%Y-%m-%d"
EXPORT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
CSV_DELIMITER = ","
JSON_INDENT = 4

# Logging Settings
ENABLE_LOGGING = True
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "fvg_trading.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Cache Settings
ENABLE_CACHING = True
CACHE_EXPIRY = 300  # seconds
MAX_CACHE_SIZE = 100  # entries

# Performance Settings
MAX_CONCURRENT_REQUESTS = 10
ENABLE_DATA_COMPRESSION = True
OPTIMIZE_DATABASE_QUERIES = True

# Feature Flags
ENABLE_ADVANCED_CHARTS = True
ENABLE_BACKTESTING = False  # Future feature
ENABLE_PAPER_TRADING = False  # Future feature
ENABLE_MULTI_SYMBOL_MONITORING = False  # Future feature
ENABLE_AUTOMATED_TRADING = False  # Future feature

# Deployment Settings
PRODUCTION_MODE = os.getenv('PRODUCTION', 'False').lower() == 'true'
DEBUG_MODE = os.getenv('DEBUG', 'True').lower() == 'true'
PORT = int(os.getenv('PORT', 8501))
HOST = os.getenv('HOST', '0.0.0.0')

# Security Settings
ENABLE_HTTPS = PRODUCTION_MODE
ENABLE_CSRF_PROTECTION = True
ENABLE_XSS_PROTECTION = True
SECURE_COOKIES = PRODUCTION_MODE

# Database Backup Settings
AUTO_BACKUP_ENABLED = True
BACKUP_INTERVAL = timedelta(days=1)
MAX_BACKUP_FILES = 7
BACKUP_DIRECTORY = "backups"

# Error Messages
ERROR_MESSAGES = {
    'invalid_symbol': 'Invalid trading symbol. Please check the symbol and try again.',
    'api_error': 'Failed to fetch data from Binance API. Please try again later.',
    'database_error': 'Database error occurred. Please contact support.',
    'authentication_failed': 'Invalid username or password.',
    'registration_failed': 'Registration failed. Username or email may already exist.',
    'webhook_invalid': 'Invalid Discord webhook URL.',
    'price_level_limit': f'Maximum price levels limit reached ({MAX_PRICE_LEVELS_PER_USER}).',
    'session_expired': 'Your session has expired. Please login again.',
}

# Success Messages
SUCCESS_MESSAGES = {
    'login_success': 'Login successful! Welcome back.',
    'registration_success': 'Registration successful! Please login.',
    'settings_saved': 'Settings saved successfully.',
    'level_added': 'Price level added successfully.',
    'level_deleted': 'Price level deleted successfully.',
    'notification_sent': 'Notification sent successfully.',
    'export_success': 'Data exported successfully.',
}

# Validation Patterns
REGEX_EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
REGEX_USERNAME = r'^[a-zA-Z0-9_]{3,20}$'
REGEX_DISCORD_WEBHOOK = r'^https://discord\.com/api/webhooks/\d+/[\w-]+$'
REGEX_SYMBOL = r'^[A-Z0-9]{4,20}$'

# Default User Preferences
DEFAULT_USER_PREFERENCES = {
    'theme': 'dark',
    'chart_type': 'candlestick',
    'show_volume': True,
    'show_indicators': True,
    'notifications_enabled': True,
    'auto_refresh': True,
    'sound_alerts': False,
}

# System Limits
MAX_USERS = 10000  # For scalability planning
MAX_SIGNALS_PER_DAY = 1000  # Per user
MAX_API_CALLS_PER_USER_PER_HOUR = 500

# Contact Information
SUPPORT_EMAIL = "support@fvgtrading.com"
DOCUMENTATION_URL = "https://docs.fvgtrading.com"
GITHUB_REPO = "https://github.com/fvgtrading/platform"

# Legal
TERMS_OF_SERVICE_URL = "https://fvgtrading.com/terms"
PRIVACY_POLICY_URL = "https://fvgtrading.com/privacy"
