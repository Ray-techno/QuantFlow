import streamlit as st
import json
from streamlit_ace import st_ace

def indicator_library_ui(indicator_engine, db_manager, user_id):
    """Show indicator library with categories"""
    
    st.subheader("📚 Indicator Library")
    
    library = indicator_engine.get_indicator_library()
    
    # Category tabs
    categories = {}
    for ind in library['builtin']:
        cat = ind['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ind)
    
    # Add custom category
    if library['custom']:
        categories['My Indicators'] = library['custom']
    
    tabs = st.tabs(list(categories.keys()))
    
    for i, (category, indicators) in enumerate(categories.items()):
        with tabs[i]:
            for ind in indicators:
                with st.expander(f"📊 {ind['name']}", expanded=False):
                    st.caption(f"Type: {ind.get('type', 'builtin')}")
                    
                    # Get indicator ID - handle different key names
                    ind_id = ind.get('id') or ind.get('indicator_id') or ind.get('name', '').replace(' ', '_').lower()
                    
                    # Show parameters - FIX: Handle both dict and string params
                    params = {}
                    if ind.get('params'):
                        # Parse params if it's a string
                        ind_params = ind['params']
                        if isinstance(ind_params, str):
                            try:
                                ind_params = json.loads(ind_params)
                            except json.JSONDecodeError:
                                ind_params = {}
                        
                        if isinstance(ind_params, dict) and ind_params:
                            st.write("**Parameters:**")
                            for param_name, default_val in ind_params.items():
                                params[param_name] = st.number_input(
                                    param_name.capitalize(),
                                    value=float(default_val) if isinstance(default_val, (int, float)) else 14.0,
                                    key=f"{ind_id}_{param_name}"
                                )
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📈 Apply to Chart", key=f"apply_{ind_id}"):
                            # Save to applied indicators
                            applied_data = {
                                'indicator_id': ind_id,
                                'indicator_type': ind.get('type', 'builtin'),
                                'params': params,
                                'config': {
                                    'color': '#2962FF',
                                    'overlay': True
                                }
                            }
                            db_manager.save_applied_indicator(user_id, applied_data)
                            st.success(f"{ind['name']} applied!")
                            st.rerun()
                    
                    with col2:
                        if st.button("🔔 Add Alert", key=f"alert_{ind_id}"):
                            st.session_state['adding_alert'] = ind_id
                            st.session_state['adding_alert_name'] = ind['name']
                            st.rerun()
                    
                    with col3:
                        if ind.get('type') != 'builtin':
                            if st.button("✏️ Edit", key=f"edit_{ind_id}"):
                                st.session_state['editing_indicator'] = ind_id
                                st.rerun()

def code_editor_ui(indicator_engine, db_manager, user_id):
    """Python code editor for custom indicators"""
    
    st.subheader("🐍 Python Code Editor")
    
    # Load indicator if editing
    if 'editing_indicator' in st.session_state:
        ind_id = st.session_state['editing_indicator']
        code = indicator_engine.get_indicator_code(ind_id)
        name = "Edit Indicator"
    else:
        code = '''def calculate(df, period=14):
    """
    Custom Indicator
    
    Parameters:
    - df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
    - period: Calculation period
    
    Returns:
    - pd.Series or pd.DataFrame with indicator values
    """
    # Your code here
    result = df['close'].rolling(window=period).mean()
    return result
'''
        name = "New Indicator"
    
    # Indicator name
    indicator_name = st.text_input("Indicator Name", value=name)
    
    # Category
    category = st.selectbox(
        "Category",
        ["Trend", "Momentum", "Volatility", "Volume", "Custom"]
    )
    
    # Code editor
    st.write("**Python Code:**")
    st.caption("Available: pd (pandas), np (numpy), df (OHLCV data)")
    
    edited_code = st_ace(
        value=code,
        language='python',
        theme='monokai',
        height=400,
        key='indicator_code_editor'
    )
    
    # Parameters
    st.write("**Default Parameters (JSON):**")
    params_json = st.text_area(
        "Parameters",
        value='{"period": 14}',
        height=100
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Indicator", type="primary"):
            try:
                params = json.loads(params_json)
                indicator_data = {
                    'name': indicator_name,
                    'code': edited_code,
                    'category': category,
                    'params': params
                }
                
                if 'editing_indicator' in st.session_state:
                    db_manager.update_custom_indicator(
                        st.session_state['editing_indicator'],
                        indicator_data
                    )
                    st.success("Indicator updated!")
                    del st.session_state['editing_indicator']
                else:
                    db_manager.save_custom_indicator(user_id, indicator_data)
                    st.success("Indicator saved!")
                
                st.rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON in parameters")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        if st.button("🧪 Test Code"):
            # Test indicator with sample data
            st.info("Testing indicator...")
            try:
                import pandas as pd
                import numpy as np
                
                # Create sample data
                sample_df = pd.DataFrame({
                    'open': np.random.randn(100).cumsum() + 100,
                    'high': np.random.randn(100).cumsum() + 102,
                    'low': np.random.randn(100).cumsum() + 98,
                    'close': np.random.randn(100).cumsum() + 100,
                    'volume': np.random.randint(1000, 10000, 100)
                })
                
                params = json.loads(params_json)
                result = indicator_engine.execute_indicator(edited_code, sample_df, params)
                
                st.success("✅ Code executed successfully!")
                st.write("**Sample Output:**")
                st.dataframe(result.tail(10))
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with col3:
        if st.button("🗑️ Clear"):
            if 'editing_indicator' in st.session_state:
                del st.session_state['editing_indicator']
            st.rerun()

def alert_manager_ui(db_manager, user_id):
    """Manage indicator alerts"""
    
    st.subheader("🔔 Alert Manager")
    
    # Add new alert
    if 'adding_alert' in st.session_state:
        st.write(f"**Add Alert for: {st.session_state.get('adding_alert_name', 'Indicator')}**")
        
        alert_type = st.selectbox(
            "Alert Type",
            ["Value", "Crossover", "Compare Lines"]
        )
        
        if alert_type == "Value":
            condition = st.selectbox("Condition", ["Above", "Below", "Equals"])
            value = st.number_input("Threshold Value", value=50.0)
            
            alert_config = {
                'indicator_id': st.session_state['adding_alert'],
                'indicator_name': st.session_state['adding_alert_name'],
                'alert_type': 'value',
                'condition': condition.lower(),
                'value': value
            }
        
        elif alert_type == "Crossover":
            condition = st.selectbox("Condition", ["Crosses Above", "Crosses Below"])
            value = st.number_input("Threshold Value", value=50.0)
            
            alert_config = {
                'indicator_id': st.session_state['adding_alert'],
                'indicator_name': st.session_state['adding_alert_name'],
                'alert_type': 'crossover',
                'condition': condition.lower().replace(" ", "_"),
                'value': value
            }
        
        else:  # Compare Lines
            condition = st.selectbox("Condition", ["Main Crosses Above Signal", "Main Crosses Below Signal"])
            
            alert_config = {
                'indicator_id': st.session_state['adding_alert'],
                'indicator_name': st.session_state['adding_alert_name'],
                'alert_type': 'compare',
                'condition': 'crosses_above' if 'Above' in condition else 'crosses_below',
                'compare_with': 'signal'
            }
        
        # Discord webhook for this alert
        webhook = st.text_input("Discord Webhook (optional)", type="password")
        if webhook:
            alert_config['webhook_url'] = webhook
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Alert", type="primary"):
                db_manager.save_indicator_alert(user_id, alert_config)
                st.success("Alert created!")
                del st.session_state['adding_alert']
                if 'adding_alert_name' in st.session_state:
                    del st.session_state['adding_alert_name']
                st.rerun()
        
        with col2:
            if st.button("Cancel"):
                del st.session_state['adding_alert']
                if 'adding_alert_name' in st.session_state:
                    del st.session_state['adding_alert_name']
                st.rerun()
        
        st.divider()
    
    # Show existing alerts
    st.write("**Active Alerts:**")
    alerts = db_manager.get_indicator_alerts(user_id)
    
    if alerts:
        for alert in alerts:
            with st.expander(f"🔔 {alert['indicator_name']} - {alert['condition']}", expanded=False):
                st.write(f"**Type:** {alert['alert_type']}")
                st.write(f"**Condition:** {alert['condition']}")
                if alert.get('value'):
                    st.write(f"**Threshold:** {alert['value']}")
                if alert.get('last_triggered'):
                    st.write(f"**Last Triggered:** {alert['last_triggered']}")
                
                if st.button("🗑️ Delete", key=f"del_alert_{alert['alert_id']}"):
                    db_manager.delete_indicator_alert(alert['alert_id'], user_id)
                    st.rerun()
    else:
        st.info("No alerts configured")

def applied_indicators_ui(db_manager, user_id):
    """Show and manage indicators applied to chart"""
    
    st.subheader("📊 Applied Indicators")
    
    applied = db_manager.get_applied_indicators(user_id)
    
    if applied:
        for app in applied:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{app['indicator_id']}**")
                if app.get('params'):
                    st.caption(f"Params: {app['params']}")
            
            with col2:
                if st.button("❌", key=f"remove_{app['applied_id']}"):
                    db_manager.delete_applied_indicator(app['applied_id'], user_id)
                    st.success("Removed from chart")
                    st.rerun()
    else:
        st.info("No indicators applied")

def indicator_manager_page(indicator_engine, db_manager, user_id):
    """Main indicator manager page"""
    
    st.title("📊 Indicators & Strategies")
    
    tabs = st.tabs(["📚 Library", "🐍 Code Editor", "🔔 Alerts", "📈 Applied"])
    
    with tabs[0]:
        indicator_library_ui(indicator_engine, db_manager, user_id)
    
    with tabs[1]:
        code_editor_ui(indicator_engine, db_manager, user_id)
    
    with tabs[2]:
        alert_manager_ui(db_manager, user_id)
    
    with tabs[3]:
        applied_indicators_ui(db_manager, user_id)
