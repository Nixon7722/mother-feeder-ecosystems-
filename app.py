import streamlit as st, json, websocket, os
from datetime import datetime
import pandas as pd
import altair as alt

st.set_page_config(page_title='MOTHER V14.4 - SNIPER LIVE', layout="wide")
st.title('🎯 MOTHER V14.4 - SNIPER LIVE - AUTO TRADING')

APP_ID = "1089"
TOKEN = os.environ.get('DERIV_TOKEN') or (st.secrets.get('DERIV_TOKEN','') if hasattr(st,'secrets') else '')
if not TOKEN:
    TOKEN = os.getenv("DERIV_TOKEN","")

if not TOKEN:
    st.warning("⚠️ DERIV_TOKEN not found! Add it in Render > Environment")
    st.stop()

# Symbol mapping
SYMBOLS = {
    "R_100": "R_100",
    "R_75": "R_75",
    "R_50": "R_50",
    "R_25": "R_25",
    "R_10": "R_10",
    "Volatility 100 Index": "R_100",
    "Volatility 75 Index": "R_75"
}

def get_candles(sym, count=100):
    try:
        ws = websocket.create_connection(f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}", timeout=10)
        req = {"ticks_history": sym, "count": count, "end": "latest", "style": "candles", "granularity": 60}
        ws.send(json.dumps(req))
        res = json.loads(ws.recv())
        ws.close()
        if 'candles' in res:
            return pd.DataFrame(res['candles'])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def deriv_buy(symbol, contract_type, stake=1):
    """contract_type = CALL or PUT, stake in USD"""
    try:
        ws = websocket.create_connection(f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}", timeout=15)
        # Auth
        ws.send(json.dumps({"authorize": TOKEN}))
        auth_res = json.loads(ws.recv())
        if 'error' in auth_res:
            ws.close()
            return False, auth_res['error']['message']
        
        # Proposal
        proposal_req = {
            "proposal": 1,
            "amount": stake,
            "basis": "stake",
            "contract_type": contract_type,
            "currency": "USD",
            "duration": 5,
            "duration_unit": "t",
            "symbol": symbol
        }
        ws.send(json.dumps(proposal_req))
        prop_res = json.loads(ws.recv())
        
        if 'error' in prop_res:
            ws.close()
            return False, prop_res['error']['message']
        
        # Buy
        buy_req = {"buy": prop_res['proposal']['id'], "price": stake}
        ws.send(json.dumps(buy_req))
        buy_res = json.loads(ws.recv())
        ws.close()
        
        if 'error' in buy_res:
            return False, buy_res['error']['message']
        return True, buy_res['buy']['contract_id']
    except Exception as e:
        return False, str(e)

def get_balance():
    try:
        ws = websocket.create_connection(f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}", timeout=10)
        ws.send(json.dumps({"authorize": TOKEN}))
        json.loads(ws.recv())
        ws.send(json.dumps({"balance": 1}))
        res = json.loads(ws.recv())
        ws.close()
        return res.get('balance',{}).get('balance',0)
    except:
        return 0

# --- UI ---
st.sidebar.header("Settings")
symbol_name = st.sidebar.selectbox("Symbol", list(SYMBOLS.keys()), index=1) # Default R_75 FAST!
symbol = SYMBOLS[symbol_name]
count = st.sidebar.slider("Candle Count", 50, 500, 100)
stake = st.sidebar.number_input("Stake $", 0.35, 100.0, 1.0)
auto_trade = st.sidebar.checkbox("🤖 AUTO TRADE ON", value=False)

balance = get_balance()
st.sidebar.metric("Balance", f"${balance}")

col1, col2, col3 = st.columns(3)
buy_btn = col1.button("🟢 BUY (CALL) - UP")
sell_btn = col2.button("🔴 SELL (PUT) - DOWN")
signal_btn = col3.button("🚀 GET SNIPER SIGNAL")

# Manual Buy/Sell
if buy_btn:
    ok, msg = deriv_buy(symbol, "CALL", stake)
    if ok:
        st.success(f"✅ BUY placed! Contract ID: {msg}")
        st.balloons()
    else:
        st.error(f"❌ Buy failed: {msg}")

if sell_btn:
    ok, msg = deriv_buy(symbol, "PUT", stake)
    if ok:
        st.success(f"✅ SELL placed! Contract ID: {msg}")
        st.balloons()
    else:
        st.error(f"❌ Sell failed: {msg}")

if signal_btn or auto_trade:
    df = get_candles(symbol, count)
    if not df.empty:
        st.success(f"Fetched {len(df)} candles for {symbol_name} ({symbol})")
        
        # Simple sniper logic: if last close > previous = UP trend
        last_close = df.iloc[-1]['close']
        prev_close = df.iloc[-2]['close']
        
        if last_close > prev_close:
            st.info(f"📈 SNIPER SIGNAL: BUY / CALL - Price going UP {prev_close} -> {last_close}")
            if auto_trade:
                ok, msg = deriv_buy(symbol, "CALL", stake)
                if ok:
                    st.success(f"🤖 AUTO BUY executed! ID: {msg}")
                else:
                    st.error(f"Auto Buy failed: {msg}")
        else:
            st.info(f"📉 SNIPER SIGNAL: SELL / PUT - Price going DOWN {prev_close} -> {last_close}")
            if auto_trade:
                ok, msg = deriv_buy(symbol, "PUT", stake)
                if ok:
                    st.success(f"🤖 AUTO SELL executed! ID: {msg}")
                else:
                    st.error(f"Auto Sell failed: {msg}")

        chart = alt.Chart(df).mark_line().encode(x='epoch:T', y='close:Q').properties(height=400)
        st.altair_chart(chart, use_container_width=True)
        st.dataframe(df.tail(10))
    else:
        st.error("No candles - check symbol")

st.caption(f"App ID {APP_ID} | {datetime.now()} | DEMO ACCOUNT ONLY - Start with $1")
