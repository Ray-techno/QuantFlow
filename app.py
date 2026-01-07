import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import json

# Import all modules
from database import DatabaseManager
from auth import AuthManager
from trading import TradingEngine
from binance_api import BinanceAPI
from notifications import NotificationManager
from indicator import IndicatorEngine

# Try to import indicator UI with ace editor, fallback to simple version
try:
    from indicator_ui import indicator_manager_page
    EDITOR_TYPE = "ace"
except ImportError:
    from indicator_ui_simple import code_editor_simple, indicator_library_ui, alert_manager_ui, applied_indicators_ui
    EDITOR_TYPE = "simple"
    st.warning("⚠️ Advanced code editor not available. Using simple text editor. Install: pip install streamlit-ace")

st.set_page_config(page_title="FVG Trading Platform", page_icon="📈", layout="wide")

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'price_levels' not in st.session_state:
    st.session_state.price_levels = []
if 'user_settings' not in st.session_state:
    st.session_state.user_settings = {}
if 'monitoring' not in st.session_state:
    st.session_state.monitoring = False
if 'signals_count' not in st.session_state:
    st.session_state.signals_count = 0
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
if 'current_price' not in st.session_state:
    st.session_state.current_price = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'chart'

# Initialize managers
db_manager = DatabaseManager()
auth_manager = AuthManager(db_manager)
binance_api = BinanceAPI()
notification_manager = NotificationManager(db_manager)
trading_engine = TradingEngine(db_manager, notification_manager)
indicator_engine = IndicatorEngine(db_manager)

def load_css(theme='dark'):
    if theme == 'dark':
        st.markdown("""
        <style>
        .stApp { background: #131722; color: #D1D4DC; }
        .stSidebar { background: #1E222D !important; }
        .metric-card { background: #1E222D; padding: 1rem; border-radius: 8px; text-align: center; }
        .badge { display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; margin: 2px; }
        .badge-blue { background: #2962FF; color: white; }
        .badge-green { background: #26A69A; color: white; }
        .badge-red { background: #EF5350; color: white; }
        .info-box { background: #1E222D; border-left: 3px solid #2962FF; padding: 10px; border-radius: 4px; margin: 10px 0; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background: #FFFFFF; color: #1a1a1a; }
        .stSidebar { background: #f5f5f5 !important; }
        .metric-card { background: #f8f9fa; padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid #e0e0e0; }
        .badge { display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; margin: 2px; }
        .badge-blue { background: #2962FF; color: white; }
        .badge-green { background: #26A69A; color: white; }
        .badge-red { background: #EF5350; color: white; }
        .info-box { background: #e3f2fd; border-left: 3px solid #2962FF; padding: 10px; border-radius: 4px; margin: 10px 0; }
        </style>
        """, unsafe_allow_html=True)

def get_fvg_type_indicator(price_level, current_price):
    """Determine FVG type based on price position"""
    if current_price is None:
        return "⚪ Unknown"
    if price_level > current_price * 1.001:
        return "🔴 Bearish"
    elif price_level < current_price * 0.999:
        return "🟢 Bullish"
    else:
        return "🟡 Both"

def login_page():
    load_css(st.session_state.theme)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 FVG Trading Platform")
        st.caption("Fair Value Gap Detection & Custom Indicators")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Login", width="stretch", type="primary"):
                if username and password:
                    user = auth_manager.authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user['user_id']
                        st.session_state.username = user['username']
                        st.session_state.user_settings = db_manager.get_user_settings(user['user_id'])
                        st.session_state.price_levels = db_manager.get_price_levels(user['user_id'])
                        st.success(f"Welcome {username}!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        
        with tab2:
            new_user = st.text_input("Username", key="reg_user")
            new_email = st.text_input("Email", key="reg_email")
            new_pass = st.text_input("Password", type="password", key="reg_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm")
            
            if st.button("Register", width="stretch", type="primary"):
                if new_user and new_email and new_pass and confirm_pass:
                    if new_pass != confirm_pass:
                        st.error("Passwords don't match")
                    elif len(new_pass) < 8:
                        st.error("Password must be 8+ characters")
                    else:
                        success, msg = auth_manager.register_user(new_user, new_email, new_pass)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)

def navigation_menu():
    """Top navigation menu"""
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    
    with col1:
        st.markdown(f"### 👤 {st.session_state.username}")
    
    with col2:
        if st.button("📊 Chart", use_container_width=True):
            st.session_state.current_page = 'chart'
            st.rerun()
    
    with col3:
        if st.button("📈 Indicators", use_container_width=True):
            st.session_state.current_page = 'indicators'
            st.rerun()
    
    with col4:
        theme_icon = "🌙" if st.session_state.theme == 'dark' else "☀️"
        if st.button(theme_icon, use_container_width=True):
            st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
            st.rerun()
    
    with col5:
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.divider()

def sidebar_controls():
    """Sidebar for settings and controls"""
    with st.sidebar:
        st.subheader("⚙️ Settings")
        
        symbol = st.text_input("Symbol", value=st.session_state.user_settings.get('symbol', 'BTCUSDT'))
        
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Price TF")
            price_tf = st.selectbox(
                "ptf", 
                ['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
                index=['1m', '5m', '15m', '30m', '1h', '4h', '1d'].index(
                    st.session_state.user_settings.get('timeframe', '15m')
                ),
                label_visibility="collapsed"
            )
        with col2:
            st.caption("FVG TF")
            fvg_tf = st.selectbox(
                "ftf",
                ['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
                index=['1m', '5m', '15m', '30m', '1h', '4h', '1d'].index(
                    st.session_state.user_settings.get('fvg_timeframe', '5m')
                ),
                label_visibility="collapsed"
            )
        
        webhook = st.text_input("Discord Webhook", 
                               value=db_manager.decrypt_webhook(st.session_state.user_id) or "",
                               type="password")
        
        refresh = st.slider("Refresh (s)", 5, 60, 
                          st.session_state.user_settings.get('refresh_interval', 5))
        
        if st.button("💾 Save Settings", width="stretch"):
            settings = {
                'symbol': symbol,
                'timeframe': price_tf,
                'fvg_timeframe': fvg_tf,
                'refresh_interval': refresh
            }
            db_manager.save_user_settings(st.session_state.user_id, settings)
            if webhook:
                db_manager.encrypt_webhook(webhook, st.session_state.user_id)
            st.session_state.user_settings = settings
            st.success("Saved!")
        
        st.divider()
        
        # Current price display
        if st.session_state.current_price:
            st.markdown(f"""
            <div class='info-box'>
                <b>Current Price</b><br>
                ${st.session_state.current_price:,.2f}
            </div>
            """, unsafe_allow_html=True)
        
        # Price Levels
        st.subheader("📊 Price Levels")
        with st.expander("➕ Add Level"):
            new_price = st.number_input("Price", min_value=0.0, step=0.01, key="new_price_input")
            
            if new_price > 0 and st.session_state.current_price:
                fvg_indicator = get_fvg_type_indicator(new_price, st.session_state.current_price)
                st.info(f"**Expected FVG:** {fvg_indicator}")
            
            new_label = st.text_input("Label (optional)")
            new_color = st.color_picker("Color", "#2962FF")
            
            if st.button("Add Level", width="stretch"):
                if new_price > 0:
                    level = {
                        'price': new_price,
                        'label': new_label or f"${new_price:,.2f}",
                        'color': new_color,
                        'enabled': True,
                        'triggered': False
                    }
                    db_manager.save_price_level(st.session_state.user_id, level)
                    st.success("Level added!")
                    st.rerun()
        
        levels = db_manager.get_price_levels(st.session_state.user_id)
        
        if levels:
            st.caption(f"{len(levels)} level(s)")
            for level in levels:
                col1, col2 = st.columns([4, 1])
                with col1:
                    icon = "✅" if level['enabled'] else "⏸️"
                    hit = "🎯" if level['triggered'] else ""
                    fvg_type = get_fvg_type_indicator(level['price'], st.session_state.current_price)
                    fvg_emoji = fvg_type.split()[0]
                    st.write(f"{icon}{hit}{fvg_emoji} **${level['price']:,.2f}**")
                with col2:
                    if st.button("×", key=f"del_{level['level_id']}"):
                        db_manager.delete_price_level(level['level_id'], st.session_state.user_id)
                        st.rerun()
            
            if st.button("🗑️ Clear All", width="stretch"):
                for lvl in levels:
                    db_manager.delete_price_level(lvl['level_id'], st.session_state.user_id)
                st.rerun()
        
        st.divider()
        
        # Monitoring control
        if not st.session_state.monitoring:
            if st.button("▶️ Start Monitoring", width="stretch", type="primary"):
                st.session_state.monitoring = True
                st.rerun()
        else:
            if st.button("⏸️ Stop Monitoring", width="stretch"):
                st.session_state.monitoring = False
                st.rerun()
    
    return symbol, price_tf, fvg_tf, refresh, levels

def check_indicator_alerts(df, applied_indicators):
    """Check all indicator alerts"""
    alerts = db_manager.get_indicator_alerts(st.session_state.user_id)
    
    for alert in alerts:
        try:
            # Get indicator code
            ind_id = alert['indicator_id']
            if ind_id in indicator_engine.builtin_indicators:
                code = indicator_engine.builtin_indicators[ind_id]['code']
                params = indicator_engine.builtin_indicators[ind_id]['params']
            else:
                code = db_manager.get_indicator_code(ind_id)
                params = {}
            
            # Execute indicator
            indicator_data = indicator_engine.execute_indicator(code, df, params)
            
            # Check alert condition
            alert_config = {
                'type': alert['alert_type'],
                'condition': alert['condition'],
                'value': alert.get('value', 0)
            }
            
            triggered, details = indicator_engine.check_alert_conditions(indicator_data, alert_config)
            
            if triggered:
                # Send notification
                webhook = alert.get('webhook_url') or db_manager.decrypt_webhook(st.session_state.user_id)
                if webhook:
                    notification_data = {
                        'indicator_name': alert['indicator_name'],
                        'condition': alert['condition'],
                        'details': details,
                        'symbol': st.session_state.user_settings.get('symbol'),
                        'timeframe': st.session_state.user_settings.get('timeframe')
                    }
                    # Send notification (you can create a new method in notifications.py)
                    st.success(f"🔔 Alert: {alert['indicator_name']} - {alert['condition']}")
                
                # Update last triggered
                db_manager.update_alert_triggered(alert['alert_id'])
        
        except Exception as e:
            st.error(f"Alert check error: {e}")

def create_chart_with_indicators(df, levels, applied_indicators, title):
    """Create chart with indicators overlaid"""
    theme = 'plotly_dark' if st.session_state.theme == 'dark' else 'plotly_white'
    
    # Exclude last candle
    df_display = df.iloc[:-1].copy() if len(df) > 1 else df.copy()
    
    fig = go.Figure()
    
    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df_display['timestamp'],
        open=df_display['open'],
        high=df_display['high'],
        low=df_display['low'],
        close=df_display['close'],
        name='Price',
        increasing_line_color='#26A69A',
        decreasing_line_color='#EF5350'
    ))
    
    # Price levels
    for level in levels:
        if level['enabled']:
            style = "solid" if not level['triggered'] else "dot"
            fig.add_hline(
                y=level['price'],
                line_dash=style,
                line_color=level['color'],
                annotation_text=level['label']
            )
    
    # Add indicators
    for app_ind in applied_indicators:
        try:
            ind_id = app_ind['indicator_id']
            params = app_ind.get('params', {})
            
            # Get indicator code
            if ind_id in indicator_engine.builtin_indicators:
                code = indicator_engine.builtin_indicators[ind_id]['code']
            else:
                code = db_manager.get_indicator_code(ind_id)
            
            # Execute indicator
            ind_data = indicator_engine.execute_indicator(code, df_display, params)
            
            # Plot indicator
            if isinstance(ind_data, pd.DataFrame):
                for col in ind_data.columns:
                    fig.add_trace(go.Scatter(
                        x=df_display['timestamp'],
                        y=ind_data[col],
                        name=f"{ind_id}_{col}",
                        mode='lines',
                        line=dict(width=1.5)
                    ))
            else:
                fig.add_trace(go.Scatter(
                    x=df_display['timestamp'],
                    y=ind_data,
                    name=ind_id,
                    mode='lines',
                    line=dict(width=1.5)
                ))
        except Exception as e:
            st.warning(f"Could not plot {ind_id}: {e}")
    
    fig.update_layout(
        title=title,
        template=theme,
        height=600,
        xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def chart_page(symbol, price_tf, fvg_tf, refresh, levels):
    """Main chart page with FVG detection"""
    
    st.title(f"📈 {symbol}")
    
    st.markdown(f"""
    <span class='badge badge-blue'>Price: {price_tf}</span>
    <span class='badge badge-green'>FVG: {fvg_tf}</span>
    <span class='badge badge-red'>Live Candle: Excluded</span>
    """, unsafe_allow_html=True)
    
    # Stats
    signals_count = db_manager.get_user_signal_count(st.session_state.user_id)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        price_display = f"${st.session_state.current_price:,.2f}" if st.session_state.current_price else "Loading..."
        st.markdown(f'<div class="metric-card"><div>Price</div><h3>{price_display}</h3></div>', 
                   unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div>Levels</div><h3>{len(levels)}</h3></div>', 
                   unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div>Signals</div><h3>{signals_count}</h3></div>', 
                   unsafe_allow_html=True)
    with col4:
        status = "🟢 Active" if st.session_state.monitoring else "⏸️ Stopped"
        st.markdown(f'<div class="metric-card"><div>Status</div><h3>{status}</h3></div>', 
                   unsafe_allow_html=True)
    
    st.divider()
    
    # Get applied indicators
    applied_indicators = db_manager.get_applied_indicators(st.session_state.user_id)
    
    if st.session_state.monitoring:
        try:
            # Fetch data
            price_df = binance_api.get_klines(symbol, price_tf, 200)
            fvg_df = binance_api.get_klines(symbol, fvg_tf, 200)
            
            if price_df is not None and not price_df.empty:
                # Update current price
                st.session_state.current_price = trading_engine.get_current_price(price_df)
                
                # Create chart with indicators
                fig = create_chart_with_indicators(price_df, levels, applied_indicators, 
                                                   f"{symbol} - {price_tf}")
                st.plotly_chart(fig, use_container_width=True)
                
                # Check FVG signals
                if fvg_df is not None and not fvg_df.empty:
                    signals = trading_engine.check_fvg_signals(
                        price_df, fvg_df, levels, 
                        st.session_state.user_id, symbol, price_tf, fvg_tf
                    )
                    
                    if signals:
                        for sig in signals:
                            st.success(f"""
                            🎯 **FVG Signal!**  
                            Level: ${sig['price_level']:,.2f} | Type: {sig['fvg_type']} | Expected: {sig.get('expected_type', 'N/A')}  
                            Zone: ${sig['fvg_low']:.2f} - ${sig['fvg_high']:.2f}
                            """)
                
                # Check indicator alerts
                check_indicator_alerts(price_df, applied_indicators)
            else:
                st.error("Failed to fetch data")
        
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.info("Click **Start Monitoring** in sidebar")

def indicators_page():
    """Indicators management page"""
    
    if EDITOR_TYPE == "ace":
        # Use full featured UI with ace editor
        indicator_manager_page(indicator_engine, db_manager, st.session_state.user_id)
    else:
        # Use simple UI with text area
        st.title("📊 Indicators & Strategies")
        
        tabs = st.tabs(["📚 Library", "🐍 Code Editor", "🔔 Alerts", "📈 Applied"])
        
        with tabs[0]:
            indicator_library_ui(indicator_engine, db_manager, st.session_state.user_id)
        
        with tabs[1]:
            code_editor_simple(indicator_engine, db_manager, st.session_state.user_id)
        
        with tabs[2]:
            alert_manager_ui(db_manager, st.session_state.user_id)
        
        with tabs[3]:
            applied_indicators_ui(db_manager, st.session_state.user_id)

def main_dashboard():
    load_css(st.session_state.theme)
    
    # Navigation menu at top
    navigation_menu()
    
    # Sidebar controls
    symbol, price_tf, fvg_tf, refresh, levels = sidebar_controls()
    
    # Page routing
    if st.session_state.current_page == 'chart':
        chart_page(symbol, price_tf, fvg_tf, refresh, levels)
    elif st.session_state.current_page == 'indicators':
        indicators_page()
    
    # Auto-refresh if monitoring
    if st.session_state.monitoring:
        time.sleep(refresh)
        st.rerun()

def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()
