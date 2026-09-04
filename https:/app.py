import streamlit as st, requests, json, websocket, pandas as pd

st.set_page_config(page_title="MOTHER V8", layout="wide")
st.title("🧠 MOTHER V8 - CLOSE FIXED")

TOKEN = st.secrets.get("DERIV_TOKEN", "")
APP_ID = st.secrets.get("DERIV_APP_ID", "34iR6HMxOfgO6m5LWOrAp")
ACCOUNT_ID = "DOT94422096"

if "contracts" not in st.session_state:
    st.session_state.contracts = []

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
    st.success(f"✅ CONNECTED: {otp[:40]}...")
    st.balloons()

tab1, tab2, tab3 = st.tabs(["🎯 TRADE", "📊 PROFIT TABLE", "📈 OPEN"])

with tab1:
    symbol = st.selectbox("Symbol", ["1HZ100V","1HZ10V","R_100","BOOM1000"])
    c1,c2 = st.columns(2)
    with c1: stake = st.number_input("Stake $",1.0,100.0,1.0, key="s1")
    with c2: mult = st.number_input("Mult",10,1000,40, key="m1")
    sl = st.number_input("SL $",0.5,100.0,0.5, key="sl1")
    tp = st.number_input("TP $",0.5,100.0,1.0, key="tp1")
    if st.button("🚀 BUY MULTUP", type="primary"):
        otp = get_otp(ACCOUNT_ID)
        prop = {"proposal":1,"amount":stake,"basis":"stake","contract_type":"MULTUP","currency":"USD","multiplier":mult,"underlying_symbol":symbol,"limit_order":{"stop_loss":sl,"take_profit":tp}}
        r1 = ws_req(otp, prop)
        if "proposal" in r1:
            otp2 = get_otp(ACCOUNT_ID)
            r2 = ws_req(otp2, {"buy": r1["proposal"]["id"], "price": stake})
            st.success(f"OPENED! ID: {r2.get('buy',{}).get('contract_id')}")
        else:
            st.error(f"{r1}")

with tab2:
    if st.button("Load Profit Table", key="pt"):
        otp = get_otp(ACCOUNT_ID)
        resp = ws_req(otp, {"profit_table":1,"description":1,"limit":25,"sort":"DESC"})
        tx = resp.get("profit_table",{}).get("transactions",[])
        if tx:
            df = pd.DataFrame(tx)
            st.dataframe(df, use_container_width=True)
        else:
            st.json(resp)

with tab3:
    if st.button("Load Open Positions", key="op"):
        otp = get_otp(ACCOUNT_ID)
        resp = ws_req(otp, {"portfolio":1})
        st.session_state.contracts = resp.get("portfolio",{}).get("contracts",[])
        st.json(resp)

    # Show stored contracts even after reload
    if st.session_state.contracts:
        contracts = st.session_state.contracts
        st.write(f"### {len(contracts)} OPEN")
        for c in contracts:
            st.code(f"ID {c.get('contract_id')} | {c.get('underlying_symbol')} | Buy ${c.get('buy_price')} | {c.get('contract_type')}")
    
    if st.session_state.contracts:
        if st.button("🔴 CLOSE ALL OPEN NOW", type="primary", key="close_all"):
            for c in st.session_state.contracts:
                try:
                    otp = get_otp(ACCOUNT_ID)
                    ws = websocket.create_connection(otp, timeout=15)
                    ws.send(json.dumps({"sell": c["contract_id"], "price": 0}))
                    resp = json.loads(ws.recv())
                    ws.close()
                    st.write(f"✅ Closed {c['contract_id']}: {resp.get('sell',{}).get('sold_for', resp)}")
                except Exception as e:
                    st.error(f"Failed {c['contract_id']}: {e}")
            st.session_state.contracts = []
            st.success("Done! All closed. Check Profit Table.")
