import streamlit as st, requests, json, websocket, time, pandas as pd
from datetime import datetime

st.set_page_config(page_title="MOTHER V13 HUNTER", layout="wide")
st.title("🎯 MOTHER V13 - MULTI-HUNTER $20/$50")

TOKEN = st.secrets.get("DERIV_TOKEN","")
APP_ID = st.secrets.get("DERIV_APP_ID","34iR6HMxOfgO6m5LWOrAp")
AID = "DOT94422096"

if "auto" not in st.session_state:
    st.session_state.auto=False
if "logs" not in st.session_state:
    st.session_state.logs=[]
if "lt" not in st.session_state:
    st.session_state.lt=0
if "trade_memory" not in st.session_state:
    st.session_state.trade_memory=[]
if "loss_streak" not in st.session_state:
    st.session_state.loss_streak=0
if "win_streak" not in st.session_state:
    st.session_state.win_streak=0

def otp_url():
    h={"Authorization":f"Bearer {TOKEN}","Deriv-App-ID":APP_ID}
    r=requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{AID}/otp",headers=h,timeout=20)
    return r.json()["data"]["url"]
def ws(p):
    u=otp_url()
    w=websocket.create_connection(u,timeout=15)
    w.send(json.dumps(p))
    r=json.loads(w.recv())
    w.close()
    return r
def candles(sym):
    try:
        u=otp_url()
        w=websocket.create_connection(u,timeout=15)
        w.send(json.dumps({"ticks_history":sym,"style":"candles","granularity":60,"count":120,"end":"latest"}))
        r=json.loads(w.recv())
        w.close()
        return pd.Data
