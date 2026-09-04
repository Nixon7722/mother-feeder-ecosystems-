import streamlit as st, json, websocket
from datetime import datetime
import pandas as pd

st.set_page_config(page_title='MOTHER V14.4 - FIXED', layout='wide')
st.title('MOTHER V14.4 - FIXED')

CLIENT_ID = "01a06813-896f-7ee5-934d-6b51adb1d481"
APP_ID = st.secrets.get('DERIV_APP_ID', '34iR6HMxOfgO6m5LWOrAp')
TOKEN = st.secrets.get('DERIV_TOKEN', 'pat_6604c2a51cf0555cac31e30bff808ef704d7323e12594625f2e30a389b14e440')

def get_candles(sym, count=100):
    try:
        ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
        ws = websocket.create_connection(ws_url, timeout=20)
        # Authorize
        ws.send(json.dumps({"authorize": TOKEN}))
        auth_resp = json.loads(ws.recv())
        # Request candles
        req = {"ticks_history": sym, "style": "candles", "granularity": 60, "count": count, "end": "latest"}
        ws.send(json.dumps(req))
        resp = json.loads(ws.recv())
        ws.close()
        if 'candles' in resp:
            return resp['candles']
        if 'error' in resp:
            st.error(f"{sym} Error: {resp['error'].get('message')}")
        return []
    except Exception as e:
        st.error(f"{sym} Connection failed: {e}")
        return []

hunt = st.multiselect("Hunt", ["1HZ100V", "R_100", "R_50", "R_25", "1HZ10V", "1HZ15V"], default=["1HZ100V", "R_100", "R_50"])
enable = st.checkbox("ENABLE BRAIN")

st.caption(f"App: {APP_ID} | Token: {TOKEN[:12]}... | Client: {CLIENT_ID[:8]}...")

if not TOKEN:
    st.warning("Add DERIV_TOKEN in Secrets")
else:
    st.success(f"Token loaded...{TOKEN[:8]}**** | AppID: {APP_ID}")

if enable:
    st.info(f"🧠 Brain enabled at {datetime.now().strftime('%H:%M:%S')} - Hunting: {', '.join(hunt)}")
    for sym in hunt:
        data = get_candles(sym)
        if data:
            df = pd.DataFrame(data)
            st.write(f"**{sym}** - {len(data)} candles - Last: {data[-1]['close'] if data else 'N/A'}")
            if 'close' in df.columns:
                st.line_chart(df['close'])
        else:
            st.write(f"**{sym}** - connecting...")
else:
    st.write("Tick ENABLE BRAIN to start hunting...")
