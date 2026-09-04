import streamlit as st, requests, json, time, websocket, threading, pandas as pd
from datetime import datetime

st.set_page_config(page_title="MOTHER V4 REAL", layout="wide", page_icon="🧠")
st.title("🧠 MOTHER V4 - REAL MULTIPLIERS BOT")

# --- SECRETS ---
TOKEN = st.secrets.get("DERIV_TOKEN", "")
APP_ID = st.secrets.get("DERIV_APP_ID", "34iR6HMxOfgO6m5LWOrAp")
ACCOUNT_ID = "DOT94422096" # from your screenshot, we will auto-detect anyway

if "connected" not in st.session_state:
    st.session_state.connected = False
    st.session_state.otp_url = ""
    st.session_state.accounts = []

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ MOTHER SETTINGS")
    symbol = st.selectbox("Symbol", ["1HZ100V", "1HZ10V", "R_100", "R_10", "BOOM1000"], index=0)
    stake = st.number_input("Stake $", 1.0, 100.0, 1.0)
    multiplier = st.number_input("Multiplier", 10, 1000, 40)
    sl = st.number_input("Stop Loss $", 0.5, 100.0, 0.5)
    tp = st.number_input("Take Profit $", 0.5, 100.0, 1.0)
    ema_fast = st.slider("EMA Fast", 3, 20, 5)
    ema_slow = st.slider("EMA Slow", 10, 50, 20)

def get_accounts():
    headers = {"Authorization": f"Bearer {TOKEN}", "Deriv-App-ID": APP_ID}
    r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers, timeout=20)
    r.raise_for_status()
    return r.json().get("data", [])

def get_otp_url(account_id):
    headers = {"Authorization": f"Bearer {TOKEN}", "Deriv-App-ID": APP_ID}
    url = f"https://api.derivws.com/trading/v1/options/accounts/{account_id}/otp"
    r = requests.post(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()["data"]["url"]

def place_trade(otp_ws_url, symbol, stake, multiplier, sl, tp, direction="MULTUP"):
    # direction: MULTUP or MULTDOWN
    logs = []
    try:
        ws = websocket.create_connection(otp_ws_url, timeout=20)
        # Proposal
        proposal = {
            "proposal": 1,
            "amount": float(stake),
            "basis": "stake",
            "contract_type": direction,
            "currency": "USD",
            "multiplier": int(multiplier),
            "underlying_symbol": symbol,
            "limit_order": {"stop_loss": float(sl), "take_profit": float(tp)}
        }
        ws.send(json.dumps(proposal))
        resp = json.loads(ws.recv())
        logs.append(f"Proposal: {resp}")
        
        if "proposal" in resp and "id" in resp["proposal"]:
            buy = {"buy": resp["proposal"]["id"], "price": float(stake)}
            ws.send(json.dumps(buy))
            buy_resp = json.loads(ws.recv())
            logs.append(f"Buy: {buy_resp}")
            ws.close()
            return True, buy_resp, logs
        else:
            ws.close()
            return False, resp, logs
    except Exception as e:
        return False, str(e), logs

# --- CONNECT ---
col1, col2 = st.columns(2)
with col1:
    if st.button("🔴 CONNECT & GET OTP", type="primary"):
        try:
            accs = get_accounts()
            if not accs:
                st.error("No accounts found")
            else:
                st.session_state.accounts = accs
                # use first active account (DOT94422096)
                target = accs[0]["account_id"]
                for a in accs:
                    if a["account_id"] == ACCOUNT_ID:
                        target = a["account_id"]
                        break
                otp_url = get_otp_url(target)
                st.session_state.otp_url = otp_url
                st.session_state.connected = True
                st.session_state.account_id = target
                st.success(f"✅ CONNECTED TO {target}")
                st.balloons()
        except Exception as e:
            st.error(f"Connect failed: {e}")

with col2:
    if st.session_state.connected:
        st.success(f"🟢 READY: {st.session_state.account_id} | OTP Ready")
        st.write(f"Balance from screenshot: $10006.04")
    else:
        st.warning("Not connected - click CONNECT")

# --- SHOW ACCOUNTS ---
if st.session_state.accounts:
    st.dataframe(pd.DataFrame(st.session_state.accounts))

# --- MANUAL TRADE ---
st.divider()
st.subheader("🎯 REAL TRADE - MULTIPLIERS")
c1, c2 = st.columns(2)
with c1:
    if st.button("🚀 BUY MULTUP (Up)", disabled=not st.session_state.connected):
        ok, resp, logs = place_trade(st.session_state.otp_url, symbol, stake, multiplier, sl, tp, "MULTUP")
        if ok:
            st.success(f"✅ TRADE OPENED! {resp}")
            # Need new OTP after each trade
            st.session_state.otp_url = get_otp_url(st.session_state.account_id)
        else:
            st.error(f"Failed: {resp}")
        st.json(logs)

with c2:
    if st.button("🔻 BUY MULTDOWN (Down)", disabled=not st.session_state.connected):
        ok, resp, logs = place_trade(st.session_state.otp_url, symbol, stake, multiplier, sl, tp, "MULTDOWN")
        if ok:
            st.success(f"✅ TRADE OPENED! {resp}")
            st.session_state.otp_url = get_otp_url(st.session_state.account_id)
        else:
            st.error(f"Failed: {resp}")
        st.json(logs)

st.divider()
st.caption(f"App ID: {APP_ID} | Token: pat_...{TOKEN[-6:]} | {datetime.now()} | Kisumu, KE")
