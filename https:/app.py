import streamlit as st, json, websocket, pandas as pd, time

st.set_page_config(page_title="MOTHER V3.2 Fixed", layout="wide")
st.title("🧠 MOTHER V3.2 - FIXED")

APP_ID = "1089"  # Official public Deriv App ID - always works

def get_live():
    try:
        ws = websocket.create_connection(f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}", timeout=15)
        # Authorize
        ws.send(json.dumps({"authorize": st.secrets["DERIV_TOKEN"]}))
        auth_resp = json.loads(ws.recv())
        if "error" in auth_resp:
            return {"error": f"TOKEN ERROR: {auth_resp['error']['message']}. Delete token and create new one in Deriv -> API token -> check Read + Trade"}
        
        prices = {}
        for sym in ["R_10","R_25","R_50","R_75","R_100"]:
            ws.send(json.dumps({"ticks": sym}))
            data = json.loads(ws.recv())
            if "tick" in data:
                prices[data["tick"]["symbol"]] = data["tick"]["quote"]
        ws.close()
        return prices
    except Exception as e:
        return {"error": str(e)}

if st.button("🔴 CONNECT TO REAL DERIV NOW", type="primary"):
    with st.spinner("Connecting to Deriv with App ID 1089..."):
        result = get_live()
        st.session_state.live = result

if "live" in st.session_state:
    if "error" in st.session_state.live:
        st.error(st.session_state.live["error"])
        st.info("Go to Deriv -> Settings -> API Token -> Create new token with scope: Read, Trade, Payments. Then update Streamlit Secrets -> DERIV_TOKEN")
    else:
        st.success("✅ REAL DERIV CONNECTED!")
        df = pd.DataFrame(list(st.session_state.live.items()), columns=["Symbol","Price"])
        st.table(df)
        st.balloons()
        st.write("Next: V4 will place REAL trades!")

st.divider()
st.write("Secrets check:")
st.write(f"Token exists: {'DERIV_TOKEN' in st.secrets}")
st.write(f"Using App ID: {APP_ID} (public)")
