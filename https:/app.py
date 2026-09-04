import streamlit as st, requests, json, websocket, pandas as pd
from datetime import datetime

st.set_page_config(page_title="MOTHER V5", layout="wide")
st.title("🧠 MOTHER V5 - REAL BOT + PROFIT TABLE")

TOKEN = st.secrets.get("DERIV_TOKEN", "")
APP_ID = st.secrets.get("DERIV_APP_ID", "34iR6HMxOfgO6m5LWOrAp")

if "otp_url" not in st.session_state:
    st.session_state.otp_url = ""
    st.session_state.account_id = "DOT94422096"

def get_accounts():
    headers = {"Authorization": f"Bearer {TOKEN}", "Deriv-App-ID": APP_ID}
    r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers, timeout=20)
    return r.json().get("data", [])

def get_otp(account_id):
    headers = {"Authorization": f"Bearer {TOKEN}", "Deriv-App-ID": APP_ID}
    r = requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{account_id}/otp", headers=headers, timeout=20)
    return r.json()["data"]["url"]

def ws_request(otp_url, payload):
    ws = websocket.create_connection(otp_url, timeout=15)
    ws.send(json.dumps(payload))
    resp = json.loads(ws.recv())
    ws.close()
    return resp

# --- CONNECT ---
if st.button("🔴 CONNECT & GET OTP", type="primary"):
    accs = get_accounts()
    otp = get_otp(st.session_state.account_id)
    st.session_state.otp_url = otp
    st.success(f"✅ CONNECTED OTP: {otp[:50]}...")
    st.balloons()

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🎯 TRADE", "📊 PROFIT TABLE", "📈 OPEN POSITIONS"])

with tab1:
    col1, col2 = st.columns(2)
    symbol = st.selectbox("Symbol", ["1HZ100V", "1HZ10V", "R_100"], key="sym")
    stake = st.number_input("Stake $", 1.0, 100.0, 1.0, key="stake")
    mult = st.number_input("Multiplier", 10, 1000, 40, key="mult")
    sl = st.number_input("SL $", 0.5, 100.0, 0.5, key="sl")
    tp = st.number_input("TP $", 0.5, 100.0, 1.0, key="tp")
    
    if st.button("🚀 BUY MULTUP"):
        if not st.session_state.otp_url:
            st.error("Connect first!")
        else:
            otp = st.session_state.otp_url
            # Proposal
            prop = {"proposal": 1, "amount": stake, "basis": "stake", "contract_type": "MULTUP", "currency": "USD", "multiplier": mult, "underlying_symbol": symbol, "limit_order": {"stop_loss": sl, "take_profit": tp}}
            r1 = ws_request(otp, prop)
            st.json(r1)
            if "proposal" in r1:
                # Need new OTP for buy (OTP is one-time? Actually re-use but safer new)
                otp2 = get_otp(st.session_state.account_id)
                st.session_state.otp_url = otp2
                buy = {"buy": r1["proposal"]["id"], "price": stake}
                r2 = ws_request(otp2, buy)
                st.success(f"TRADE OPENED! Contract: {r2.get('buy', {}).get('contract_id')}")
                st.json(r2)
                # refresh OTP again
                st.session_state.otp_url = get_otp(st.session_state.account_id)

with tab2:
    st.subheader("📊 Your Profit Table - Last 25 trades")
    if st.button("Load Profit Table"):
        if not st.session_state.otp_url:
            st.error("Connect first!")
        else:
            otp = get_otp(st.session_state.account_id)
            payload = {"profit_table": 1, "description": 1, "limit": 25, "sort": "DESC"}
            resp = ws_request(otp, payload)
            st.json(resp)
            if "profit_table" in resp:
                df = pd.DataFrame(resp["profit_table"]["transactions"])
                st.dataframe(df)
                total = df["sell_price"].astype(float).sum() - df["buy_price"].astype(float).sum() if "sell_price" in df.columns else 0
                st.metric("Total P/L (approx)", f"${total:.2f}")

with tab3:
    st.subheader("📈 Open Positions")
    if st.button("Load Open Positions"):
        otp = get_otp(st.session_state.account_id)
        resp = ws_request(otp, {"portfolio": 1})
        st.json(resp)

st.caption(f"Account: {st.session_state.account_id} | App: {APP_ID} | {datetime.now()}")
