import streamlit as st
import pandas as pd
import numpy as np
import time, json, os, threading, queue
from datetime import datetime
import websocket

st.set_page_config(page_title="MOTHER - Real Deriv Autonomous", layout="wide")

# --- SECRETS ---
try:
    DERIV_TOKEN = st.secrets["DERIV_TOKEN"]
    APP_ID = st.secrets.get("APP_ID", "34iR6HMxOfgO6m5LWOrAp")
    st.sidebar.success(f"Connected App ID: {APP_ID}")
except Exception as e:
    st.error("Add DERIV_TOKEN and APP_ID to Streamlit Secrets!")
    st.stop()

SYMBOLS = ["R_10","R_25","R_50","R_75","R_100","BOOM1000","CRASH1000","frxEURUSD","frxGBPUSD","frxXAUUSD"]
MEMORY_FILE = "mother_memory.json"

# --- MEMORY ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE,"r") as f:
            return json.load(f)
    return {"trades": [], "learnings": [], "balance": 10000}

def save_memory(mem):
    with open(MEMORY_FILE,"w") as f:
        json.dump(mem,f)

if "memory" not in st.session_state:
    st.session_state.memory = load_memory()
if "ticks" not in st.session_state:
    st.session_state.ticks = {s: [] for s in SYMBOLS}
if "live_prices" not in st.session_state:
    st.session_state.live_prices = {}

# --- REAL DERIV FEED ---
def on_message(ws, message):
    data = json.loads(message)
    if "tick" in data:
        symbol = data["tick"]["symbol"]
        price = float(data["tick"]["quote"])
        st.session_state.live_prices[symbol] = price
        st.session_state.ticks[symbol].append(price)
        if len(st.session_state.ticks[symbol]) > 200:
            st.session_state.ticks[symbol] = st.session_state.ticks[symbol][-200:]

def on_open(ws):
    ws.send(json.dumps({"authorize": DERIV_TOKEN}))
    for sym in SYMBOLS:
        ws.send(json.dumps({"ticks": sym, "subscribe": 1}))

def start_ws():
    url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message)
    ws.run_forever()

if "ws_started" not in st.session_state:
    threading.Thread(target=start_ws, daemon=True).start()
    st.session_state.ws_started = True

# --- UI ---
st.title("🧠 MOTHER - Real Deriv Autonomous Brain")
st.caption(f"App ID: {APP_ID} | Client: 01a06...d481 | Mode: DEMO AUTONOMOUS")

col1, col2, col3 = st.columns(3)
col1.metric("Live Symbols", len(st.session_state.live_prices))
col2.metric("Total Trades Learned", len(st.session_state.memory["trades"]))
col3.metric("Demo Balance", f"${st.session_state.memory['balance']:.2f}")

st.subheader("🔴 LIVE REAL PRICES from Deriv")
if st.session_state.live_prices:
    df_prices = pd.DataFrame(list(st.session_state.live_prices.items()), columns=["Symbol","Price"])
    st.dataframe(df_prices, use_container_width=True)
else:
    st.warning("Connecting to Deriv... wait 5-10 seconds and Refresh")

st.subheader("📈 Mother Analysis (RSI + Momentum)")
for sym, ticks in st.session_state.ticks.items():
    if len(ticks) > 14:
        arr = np.array(ticks)
        rsi = 50 # simplified
        mom = arr[-1] - arr[-10]
        signal = "BUY" if mom > 0 else "SELL"
        st.write(f"{sym}: {arr[-1]:.2f} | Mom: {mom:.4f} -> {signal}")

# --- AUTO TRADE CHILDREN (SIMULATED EXECUTION ON DEMO) ---
if st.button("▶️ START Autonomous Children (DEMO)"):
    st.session_state.auto = True

if st.session_state.get("auto", False):
    # Simple child logic: trades strongest momentum
    if st.session_state.live_prices:
        best_sym = max(st.session_state.ticks, key=lambda s: len(st.session_state.ticks[s]) and st.session_state.ticks[s][-1] - st.session_state.ticks[s][0] if len(st.session_state.ticks[s])>5 else -999)
        if len(st.session_state.ticks[best_sym]) > 5:
            price = st.session_state.live_prices.get(best_sym,0)
            trade = {
                "time": datetime.now().isoformat(),
                "symbol": best_sym,
                "price": price,
                "action": "BUY",
                "child": "Child-1-Scalper"
            }
            st.session_state.memory["trades"].append(trade)
            save_memory(st.session_state.memory)
            st.toast(f"Child traded {best_sym} @ {price}")

    st.rerun()

st.sidebar.button("🔄 Refresh Live Feed")
