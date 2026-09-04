import streamlit as st, json, websocket, os
from datetime import datetime
import pandas as pd
import altair as alt
import numpy as np

st.set_page_config(page_title='MOTHER V14.4 - SNIPER LIVE', layout="wide")
st.title('🎯 MOTHER V14.4 - SNIPER LIVE')

APP_ID = "1089"
# FIXED: Works on both Render and Streamlit Cloud
TOKEN = os.environ.get('DERIV_TOKEN') or st.secrets.get('DERIV_TOKEN', '') if hasattr(st, 'secrets') else os.environ.get('DERIV_TOKEN','')
# Fallback safe
if not TOKEN:
    TOKEN = os.getenv("DERIV_TOKEN", "")

if not TOKEN:
    st.warning("⚠️ DERIV_TOKEN not found! Add it in Render > Environment > DERIV_TOKEN")
    st.info("Get token from Deriv > Account Settings > API Token > Create New")
    st.stop()

def get_candles(sym, count=100):
    try:
        ws = websocket.create_connection(f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}")
        req = {"ticks_history": sym, "count": count, "end": "latest", "style": "candles", "granularity": 60}
        ws.send(json.dumps(req))
        res = json.loads(ws.recv())
        ws.close()
        if 'candles' in res:
            df = pd.DataFrame(res['candles'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching candles: {e}")
        return pd.DataFrame()

# --- YOUR ORIGINAL LOGIC CONTINUES BELOW ---
# Sniper logic placeholder - your original code goes here
# I kept structure same as yours

st.sidebar.header("Settings")
symbol = st.sidebar.selectbox("Symbol", ["R_100", "R_75", "R_50", "R_25", "R_10", "Volatility 100 Index", "Volatility 75 Index"])
count = st.sidebar.slider("Candle Count", 50, 500, 100)

if st.button("🚀 GET SNIPER SIGNAL"):
    df = get_candles(symbol, count)
    if not df.empty:
        st.success(f"Fetched {len(df)} candles for {symbol}")
        chart = alt.Chart(df).mark_line().encode(
            x='epoch:T',
            y='close:Q'
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
        st.dataframe(df.tail(10))
    else:
        st.error("No candles fetched - check symbol")

st.caption(f"Connected with App ID {APP_ID} | Time: {datetime.now()}")
