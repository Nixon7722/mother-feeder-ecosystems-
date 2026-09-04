import streamlit as st, json, websocket, time
from datetime import datetime
import pandas as pd
import altair as alt
import numpy as np

st.set_page_config(page_title='MOTHER V14.4 - SNIPER', layout='wide', page_icon='🎯')
st.title('🎯 MOTHER V14.4 - SNIPER LIVE')

APP_ID = "1089"
TOKEN = st.secrets.get('DERIV_TOKEN', 'pat_6604c2a51cf0555cac31e30bff808ef704d7323e12594625f2e30a389b14e440')

def get_candles(sym, count=100):
    try:
        ws = websocket.create_connection(f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}", timeout=15)
        ws.send(json.dumps({"authorize": TOKEN}))
        ws.recv()
        ws.send(json.dumps({"ticks_history": sym, "style": "candles", "granularity": 60, "count": count, "end": "latest"}))
        resp = json.loads(ws.recv())
        ws.close()
        return resp.get('candles', [])
    except:
        return []

def place_trade(symbol, contract_type, stake=1):
    """CALL or PUT"""
    try:
        ws = websocket.create_connection(f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}", timeout=15)
        ws.send(json.dumps({"authorize": TOKEN}))
        ws.recv()
        # Proposal
        proposal = {"proposal": 1, "amount": stake, "basis": "stake", "contract_type": contract_type, "currency": "USD", "duration": 1, "duration_unit": "m", "symbol": symbol}
        ws.send(json.dumps(proposal))
        prop_resp = json.loads(ws.recv())
        if 'proposal' in prop_resp:
            buy = {"buy": prop_resp['proposal']['id'], "price": stake}
            ws.send(json.dumps(buy))
            buy_resp = json.loads(ws.recv())
            ws.close()
            return buy_resp
        ws.close()
        return prop_resp
    except Exception as e:
        return {"error": str(e)}

def sniper_signal(df):
    """EMA 7/20 + RSI 14"""
    df['ema7'] = df['close'].ewm(span=7).mean()
    df['ema20'] = df['close'].ewm(span=20).mean()
    delta = df['close'].diff()
    gain = delta.where(delta>0,0).rolling(14).mean()
    loss = -delta.where(delta<0,0).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1+rs))
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # SIGNAL LOGIC
    if prev['ema7'] < prev['ema20'] and last['ema7'] > last['ema20'] and last['rsi'] < 70:
        return "CALL", f"EMA CROSS UP + RSI {last['rsi']:.1f}"
    if prev['ema7'] > prev['ema20'] and last['ema7'] < last['ema20'] and last['rsi'] > 30:
        return "PUT", f"EMA CROSS DOWN + RSI {last['rsi']:.1f}"
    return "WAIT", f"RSI {last['rsi']:.1f}"

# --- UI ---
st.sidebar.title("⚙️ Sniper Settings")
stake = st.sidebar.number_input("Stake $", 0.35, 100.0, 1.0, 0.35)
auto_trade = st.sidebar.checkbox("🔥 AUTO TRADE ON", value=False)
hunt = st.sidebar.multiselect("Hunt", ["1HZ100V", "R_100", "R_50", "R_25", "1HZ10V"], default=["1HZ100V", "R_100", "R_50"])

enable = st.checkbox("ENABLE BRAIN", value=True)

if auto_trade:
    st.sidebar.error("⚠️ LIVE MONEY - Auto trading active!")

if enable:
    st.success(f"🧠 Sniper hunting at {datetime.now().strftime('%H:%M:%S')} | Stake: ${stake} | Auto: {'ON 🔴' if auto_trade else 'OFF'}")
    
    for sym in hunt:
        data = get_candles(sym)
        if data:
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'])
            signal, reason = sniper_signal(df)
            
            last = df['close'].iloc[-1]
            
            col1, col2, col3 = st.columns([1,1,3])
            with col1:
                color_bg = "#0f3d15" if signal=="CALL" else "#3d0f0f" if signal=="PUT" else "#2a2a2a"
                emoji = "🟢 BUY" if signal=="CALL" else "🔴 SELL" if signal=="PUT" else "⏳ WAIT"
                st.markdown(f"""
                <div style="background:{color_bg};padding:15px;border-radius:12px;text-align:center;border:2px solid {'#00ff88' if signal!='WAIT' else '#555'}">
                    <b>{sym}</b><br>
                    <span style="font-size:20px">{last:.2f}</span><br>
                    <b style="font-size:18px">{emoji}</b><br>
                    <small>{reason}</small>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.metric("Signal", signal, reason)
                if st.button(f"Manual {signal} {sym}", key=f"btn_{sym}", disabled=(signal=="WAIT")):
                    res = place_trade(sym, signal, stake)
                    st.json(res)
                if auto_trade and signal != "WAIT":
                    st.warning(f"AUTO {signal} {sym}...")
                    res = place_trade(sym, signal, stake)
                    st.json(res)
                    time.sleep(2)
            with col3:
                chart = alt.Chart(df.reset_index()).mark_line(strokeWidth=2).encode(
                    x='index:Q', y=alt.Y('close:Q', scale=alt.Scale(zero=False)), tooltip=['close']
                ).properties(height=180)
                ema7 = alt.Chart(df.reset_index()).mark_line(color='yellow', strokeDash=[2,2]).encode(x='index:Q', y='ema7:Q')
                ema20 = alt.Chart(df.reset_index()).mark_line(color='red', strokeDash=[4,4]).encode(x='index:Q', y='ema20:Q')
                st.altair_chart(chart + ema7 + ema20, use_container_width=True)
            st.divider()
else:
    st.write("Enable brain to snipe")
