import streamlit as st, json, os, threading, time, websocket, pandas as pd, numpy as np
from datetime import datetime

st.set_page_config(page_title="MOTHER V3 - Real Executor", layout="wide")

DERIV_TOKEN = st.secrets["DERIV_TOKEN"]
APP_ID = st.secrets.get("APP_ID", "34iR6HMxOfgO6m5LWOrAp")
SYMBOLS = ["R_10","R_25","R_50","R_75","R_100","BOOM1000","CRASH1000","frxEURUSD","frxXAUUSD"]
MEMORY_FILE = "mother_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        return json.load(open(MEMORY_FILE))
    return {"trades":[],"balance":10000}
def save_memory(m): json.dump(m, open(MEMORY_FILE,"w"))

if "memory" not in st.session_state: st.session_state.memory = load_memory()
if "live" not in st.session_state: st.session_state.live = {}
if "ticks" not in st.session_state: st.session_state.ticks = {s:[] for s in SYMBOLS}

ws_global = None

def on_message(ws, msg):
    d = json.loads(msg)
    if "tick" in d:
        s = d["tick"]["symbol"]; p = float(d["tick"]["quote"])
        st.session_state.live[s] = p
        st.session_state.ticks[s].append(p)
        st.session_state.ticks[s] = st.session_state.ticks[s][-200:]

def on_open(ws):
    ws.send(json.dumps({"authorize": DERIV_TOKEN}))
    time.sleep(0.5)
    for s in SYMBOLS:
        ws.send(json.dumps({"ticks": s, "subscribe": 1}))
    global ws_global; ws_global = ws

def run_ws():
    websocket.WebSocketApp(f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}", on_open=on_open, on_message=on_message).run_forever()

if "started" not in st.session_state:
    threading.Thread(target=run_ws, daemon=True).start()
    st.session_state.started = True

st.title("🧠 MOTHER V3 - REAL EXECUTOR")
st.write(f"App {APP_ID} | Token active: {DERIV_TOKEN[:8]}... | Mode: DEMO REAL TRADING")

if st.session_state.live:
    st.dataframe(pd.DataFrame(list(st.session_state.live.items()), columns=["Symbol","Live Price"]))
else:
    st.warning("Connecting... wait 10s then Rerun")

def place_trade(symbol, contract_type="CALL", amount=1, duration=5):
    # This sends real proposal + buy via same ws
    try:
        ws_global.send(json.dumps({
            "proposal": 1,
            "amount": amount,
            "basis": "stake",
            "contract_type": contract_type,
            "currency": "USD",
            "duration": duration,
            "duration_unit": "t",
            "symbol": symbol
        }))
        # Note: full V3 will handle proposal_open_contract and buy - for now we log
        trade = {"time": str(datetime.now()), "symbol": symbol, "type": contract_type, "stake": amount}
        st.session_state.memory["trades"].append(trade)
        save_memory(st.session_state.memory)
        return True
    except: return False

c1,c2 = st.columns(2)
with c1:
    sym = st.selectbox("Child Symbol", SYMBOLS)
    amt = st.number_input("Stake $", 0.35, 10.0, 1.0)
    if st.button(f"BUY CALL on {sym} (Real DEMO)"):
        if place_trade(sym, "CALL", amt, 5):
            st.success(f"Real proposal sent for {sym} CALL ${amt}")

with c2:
    if st.button("🤖 MOTHER AUTONOMOUS - Start Children Trading Alone"):
        st.session_state.autonomous = True
        st.success("Mother is now autonomous - Children will trade every 15 sec")

if st.session_state.get("autonomous"):
    time.sleep(15)
    # Child logic: pick highest momentum
    if st.session_state.live:
        candidates = {k: v[-1]-v[0] for k,v in st.session_state.ticks.items() if len(v)>10}
        if candidates:
            best = max(candidates, key=candidates.get)
            place_trade(best, "CALL" if candidates[best]>0 else "PUT", 1, 5)
    st.rerun()
