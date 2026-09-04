import streamlit as st, requests, json, websocket, pandas as pd
from datetime import datetime

st.set_page_config(page_title="MOTHER V6", layout="wide")
st.title("🧠 MOTHER V6 - LIVE P/L")

TOKEN = st.secrets.get("DERIV_TOKEN", "")
APP_ID = st.secrets.get("DERIV_APP_ID", "34iR6HMxOfgO6m5LWOrAp")
ACCOUNT_ID = "DOT94422096"

if "otp_url" not in st.session_state:
    st.session_state.otp_url = ""

def get_otp(account_id):
    headers = {"Authorization": f"Bearer {TOKEN}", "Deriv-App-ID": APP_ID}
    r = requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{account_id}/otp", headers=headers, timeout=20)
    return r.json()["data"]["url"]

def ws_req(otp_url, payload):
    ws = websocket.create_connection(otp_url, timeout=15)
    ws.send(json.dumps(payload))
    resp = json.loads(ws.recv())
    ws.close()
    return resp

if st.button("🔴 CONNECT & GET OTP", type="primary"):
    otp = get_otp(ACCOUNT_ID)
    st.session_state.otp_url = otp
    st.success("✅ CONNECTED!")
    st.balloons()

tab1, tab2, tab3 = st.tabs(["🎯 TRADE", "📊 PROFIT TABLE", "📈 OPEN"])

with tab1:
    symbol = st.selectbox("Symbol", ["1HZ100V","1HZ10V","R_100","BOOM1000"])
    c1,c2 = st.columns(2)
    with c1: stake = st.number_input("Stake $",1.0,100.0,1.0)
    with c2: mult = st.number_input("Mult",10,1000,40)
    sl = st.number_input("SL $",0.5,100.0,0.5)
    tp = st.number_input("TP $",0.5,100.0,1.0)
    
    if st.button("🚀 BUY MULTUP", type="primary"):
        otp = get_otp(ACCOUNT_ID)
        st.session_state.otp_url = otp
        prop = {"proposal":1,"amount":stake,"basis":"stake","contract_type":"MULTUP","currency":"USD","multiplier":mult,"underlying_symbol":symbol,"limit_order":{"stop_loss":sl,"take_profit":tp}}
        r1 = ws_req(otp, prop)
        if "proposal" in r1:
            otp2 = get_otp(ACCOUNT_ID)
            r2 = ws_req(otp2, {"buy": r1["proposal"]["id"], "price": stake})
            st.success(f"OPENED! ID: {r2.get('buy',{}).get('contract_id')}")
            st.json(r2)
        else:
            st.error(f"{r1}")

with tab2:
    if st.button("Load Profit Table"):
        otp = get_otp(ACCOUNT_ID)
        resp = ws_req(otp, {"profit_table":1,"description":1,"limit":25,"sort":"DESC"})
        tx = resp.get("profit_table",{}).get("transactions",[])
        if tx:
            df = pd.DataFrame(tx)
            # Show key cols
            cols = [c for c in ["buy_time","contract_id","transaction_type","buy_price","sell_price","longcode","profit_loss"] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True)
            if "sell_price" in df.columns:
                try:
                    total_pl = (df["sell_price"].fillna(0).astype(float) - df["buy_price"].fillna(0).astype(float)).sum()
                    st.metric("Total P/L last 25", f"${total_pl:.2f}")
                except: pass
        else:
            st.json(resp)

with tab3:
    if st.button("Load Open Positions"):
        otp = get_otp(ACCOUNT_ID)
        resp = ws_req(otp, {"portfolio":1})
        contracts = resp.get("portfolio",{}).get("contracts",[])
        if contracts:
            df = pd.DataFrame(contracts)
            st.dataframe(df, use_container_width=True)
            for c in contracts:
                st.write(f"**ID {c.get('contract_id')}** | {c.get('underlying_symbol')} | Buy ${c.get('buy_price')} | Profit: ${c.get('profit_loss', c.get('profit', 0))} | {c.get('contract_type')}")
        else:
            st.info("No open positions or:")
            st.json(resp)
