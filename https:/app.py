import streamlit as st, requests, json, websocket, time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MOTHER V11 HUNTER", layout="wide")
st.title("🧠 MOTHER V11 - AGGRESSIVE HUNTER")

TOKEN = st.secrets.get("DERIV_TOKEN", "")
APP_ID = st.secrets.get("DERIV_APP_ID", "34iR6HMxOfgO6m5LWOrAp")
ACCOUNT_ID = "DOT94422096"

if "auto_on" not in st.session_state:
    st.session_state.auto_on = False
if "logs" not in st.session_state:
    st.session_state.logs = []
if "last_trade_time" not in st.session_state:
    st.session_state.last_trade_time = 0

def get_otp():
    headers = {"Authorization": f"Bearer {TOKEN}", "Deriv-App-ID": APP_ID}
    r = requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{ACCOUNT_ID}/otp", headers=headers, timeout=20)
    return r.json()["data"]["url"]

def ws_req(payload):
    otp = get_otp()
    ws = websocket.create_connection(otp, timeout=15)
    ws.send(json.dumps(payload))
    resp = json.loads(ws.recv())
    ws.close()
    return resp

def get_candles(symbol="1HZ100V", count=50):
    try:
        otp = get_otp()
        ws = websocket.create_connection(otp, timeout=15)
        ws.send(json.dumps({"ticks_history": symbol, "style": "candles", "granularity": 60, "count": count, "end": "latest"}))
        resp = json.loads(ws.recv())
        ws.close()
        return pd.DataFrame(resp.get("candles", []))
    except:
        return pd.DataFrame()

def buy_trade(symbol, stake, mult, sl, tp, direction="MULTUP"):
    prop = {"proposal":1,"amount":stake,"basis":"stake","contract_type":direction,"currency":"USD","multiplier":mult,"underlying_symbol":symbol,"limit_order":{"stop_loss":sl,"take_profit":tp}}
    r1 = ws_req(prop)
    if "proposal" in r1:
        r2 = ws_req({"buy": r1["proposal"]["id"], "price": stake})
        return r2
    return r1

# SIDEBAR
st.sidebar.header("⚙️ V11 HUNTER")
symbol = st.sidebar.selectbox("Symbol", ["1HZ100V","1HZ10V","R_100","R_50","BOOM1000"], index=0)
stake = st.sidebar.number_input("Stake $", 0.5, 10.0, 0.5, step=0.5)
mult = st.sidebar.number_input("Multiplier", 10, 1000, 50)
sl = st.sidebar.number_input("SL $", 0.
