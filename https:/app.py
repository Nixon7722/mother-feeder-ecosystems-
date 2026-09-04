import streamlit as st, requests, json, websocket, time, pandas as pd, os
from datetime import datetime

st.set_page_config(page_title="MOTHER V14.2", layout="wide")
st.title("MOTHER V14.2 - INFINITE BRAIN")

TOKEN = st.secrets.get("DERIV_TOKEN","")
APP_ID = st.secrets.get("DERIV_APP_ID","34iR6HMxOfgO6m5LWOrAp")
AID = "DOT94422096"
BRAIN_FILE = "mother_brain.json"

def otp_url():
    h = {"Authorization": f"Bearer {TOKEN}", "Deriv-App-ID": APP_ID}
    url = f"https://api.derivws.com/trading/v1/options/accounts/{AID}/otp"
    r = requests.post(url, headers=h, timeout=20)
    return r.json()["data"]["url"]

def ws(p):
    u = otp_url()
    w = websocket.create_connection(u, timeout=15)
    w.send(json.dumps(p))
    r = json.loads(w.recv())
    w.close()
    return r

def candles(sym):
    try:
        u = otp_url()
        w = websocket.create_connection(u, timeout=15)
        msg = {"ticks_history": sym, "style": "candles", "granularity": 60, "count": 120, "end": "latest"}
        w.send(json.dumps(msg))
        r = json.loads(w.recv())
        w.close()
        return pd.DataFrame(r.get("candles", []))
    except:
        return pd.DataFrame()

def buy(sym, stake, mult, sl, tp, typ):
    pr = {"proposal": 1, "amount": stake, "basis": "stake", "contract_type": typ, "currency": "USD", "multiplier": mult, "underlying_symbol": sym, "limit_order": {"stop_loss": sl, "take_profit": tp}}
    a = ws(pr)
    if "proposal" in a:
        b = ws({"buy": a["proposal"]["id"], "price": stake})
        return b
    return a

def rsi_calc(df):
    d = df['close'].diff()
    g = d.where(d > 0, 0).ewm(alpha=1/14).mean()
    l = (-d.where(d < 0, 0)).ewm(alpha=1/14).mean()
    rs = g / l
    return 100 - (100 / (1 + rs))

def load_brain():
    if os.path.exists(BRAIN_FILE):
        try:
            with open(BRAIN_FILE, "r") as f:
                data = json.load(f)
                return data.get("cells", []), data.get("super_cells", []), data.get("iq", 60)
        except:
            pass
    return [], [], 60

def save_brain(cells, scells, iq):
    try:
        with open(BRAIN_FILE, "w") as f:
            json.dump({"cells": cells[-2000:], "super_cells": scells[-500:], "iq": iq}, f)
    except:
        pass

def import_hist():
    try:
        r = ws({"profit_table": 1, "description": 1, "limit": 60, "sort": "DESC"})
        tx = r.get("profit_table", {}).get("transactions", [])
        cells = []
        for t in tx:
            if t.get("
