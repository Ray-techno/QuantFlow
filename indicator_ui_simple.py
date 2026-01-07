import streamlit as st
import json

def code_editor_simple(indicator_engine, db_manager, user_id):
    """
    Python code editor using simple text_area (no external dependencies)
    Use this version if streamlit-ace is not available
    """
    
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
    
    # Code editor using text_area
    st.write("**Python Code:**")
    st.caption("Available libraries: pd (pandas), np (numpy), df (OHLCV DataFrame)")
    st.caption("💡 Tip: Press Ctrl+Enter to auto-format in some browsers")
    
    edited_code = st.text_area(
        "Code",
        value=code,
        height=400,
        help="Write your indicator calculation function here",
        label_visibility="collapsed"
    )
    
    # Parameters
    st.write("**Default Parameters (JSON):**")
    params_json = st.text_area(
        "Parameters",
        value='{"period": 14}',
        height=100,
        help='Example: {"period": 14, "multiplier": 2.0}'
    )
    
    # Syntax highlighting helper
    with st.expander("📖 Python Syntax Reference"):
        st.code("""
# Common Operations:

# Moving Average
ma = df['close'].rolling(window=period).mean()

# EMA
ema = df['close'].ewm(span=period, adjust=False).mean()

# Standard Deviation
std = df['close'].rolling(window=period).std()

# Max/Min
high_max = df['high'].rolling(window=period).max()
low_min = df['low'].rolling(window=period).min()

# Percentage Change
pct_change = df['close'].pct_change()

# Cumulative Sum
cumsum = df['volume'].cumsum()

# Return DataFrame for multiple lines:
return pd.DataFrame({
    'line1': series1,
    'line2': series2
})
        """, language='python')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Indicator", type="primary", use_container_width=True):
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
                    st.success("✅ Indicator updated!")
                    del st.session_state['editing_indicator']
                else:
                    db_manager.save_custom_indicator(user_id, indicator_data)
                    st.success("✅ Indicator saved!")
                
                st.rerun()
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON in parameters")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with col2:
        if st.button("🧪 Test Code", use_container_width=True):
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
                st.write("**Sample Output (last 10 values):**")
                
                if isinstance(result, pd.DataFrame):
                    st.dataframe(result.tail(10), use_container_width=True)
                else:
                    st.dataframe(pd.DataFrame({'value': result.tail(10)}), use_container_width=True)
                
                # Show statistics
                st.caption(f"Output shape: {result.shape if hasattr(result, 'shape') else len(result)}")
                
            except Exception as e:
                st.error(f"❌ Execution Error: {str(e)}")
                with st.expander("See error details"):
                    st.code(str(e))
    
    with col3:
        if st.button("🗑️ Clear", use_container_width=True):
            if 'editing_indicator' in st.session_state:
                del st.session_state['editing_indicator']
            st.rerun()
    
    # Code examples
    with st.expander("💡 Code Examples"):
        st.write("**Example 1: Simple Moving Average**")
        st.code("""
def calculate(df, period=20):
    return df['close'].rolling(window=period).mean()
        """, language='python')
        
        st.write("**Example 2: RSI**")
        st.code("""
def calculate(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
        """, language='python')
        
        st.write("**Example 3: Bollinger Bands (Multi-line)**")
        st.code("""
def calculate(df, period=20, std=2):
    sma = df['close'].rolling(window=period).mean()
    std_dev = df['close'].rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return pd.DataFrame({
        'upper': upper,
        'middle': sma,
        'lower': lower
    })
        """, language='python')

# Use this version in main app if streamlit-ace is not available:
# from indicator_ui_simple import code_editor_simple
# code_editor_simple(indicator_engine, db_manager, user_id)
