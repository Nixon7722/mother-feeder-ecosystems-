import streamlit as st, json, os, time, websocket, pandas as pd
from datetime import datetime

st.set_page_config(page_title="MOTHER V3.1", layout="wide")
st.title("🧠 MOTHER V3 - REAL EXECUTOR")
st.caption(f"App {st.secrets.get('APP_ID')} | Mode: DEMO REAL")

SYMBOLS = ["R_10","R_25","R_50","R_75","R_100"]

def get_live_prices():
    try:
        ws = websocket.create_connection(f"wss://ws.derivws.com/websockets/v3?app_id={st.secrets['APP_ID']}", timeout=10)
        ws.send(json.dumps({"authorize": st.secrets["DERIV_TOKEN"]}))
        auth = json.loads(ws.recv())
        # print(auth)
        prices = {}
        for sym in SYMBOLS:
            ws.send(json.dumps({"ticks": sym}))
            tick_data = json.loads(ws.recv())
            if "tick" in tick_data:
                prices[tick_data["tick"]["symbol"]] = tick_data["tick"]["quote"]
        ws.close()
        return prices
    except Exception as e:
        return {"error": str(e)}

# --- LIVE FETCH ---
if st.button("🔴 CONNECT TO REAL DERIV NOW"):
    with st.spinner("Authorizing with Deriv..."):
        prices = get_live_prices()
        st.session_state.live = prices
        st.success("Connected!")

if "live" in st.session_state and st.session_state.live:
    if "error" in st.session_state.live:
        st.error(f"Error: {st.session_state.live['error']}")
        st.info("Check if Token is correct in Secrets, and App ID 34iR6HMxOfgO6m5LWOrAp is approved")
    else:
        st.subheader("✅ REAL DERIV PRICES - LIVE")
        df = pd.DataFrame(list(st.session_state.live.items()), columns=["Symbol","Price"])
        st.dataframe(df, use_container_width=True)
        st.metric("R_10", st.session_state.live.get("R_10","-"))
        st.balloons()

# --- TRADE ---
st.divider()
sym = st.selectbox("Child Symbol", SYMBOLS)
amt = st.number_input("Stake $", 0.35, 5.0, 1.0)

if st.button(f"BUY CALL {sym} - REAL DEMO"):
    st.warning("V4 will execute real BUY. V3.1 confirms connection first. Connection OK? Then we go V4.")

st.button("🤖 MOTHER AUTONOMOUS ON")

st.autorefresh = st.empty()
time.sleep(5)
st.rerun()
