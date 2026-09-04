import streamlit as st, json, websocket
from datetime import datetime
import pandas as pd

st.set_page_config(page_title='MOTHER V14.4 - FIXED', layout='wide')
st.title('MOTHER V14.4 - FIXED')

CLIENT_ID = "01a06813-896f-7ee5-934d-6b51adb1d481"
# Use public valid Deriv AppID 1089 (yours 34iR... is OAuth client, not websocket app_id)
APP_ID = "1089"
TOKEN = st.secrets.get('DERIV_TOKEN', 'pat_6604c2a51cf0555cac31e30bff808ef704d7323e12594625f2e30a389b14e440')

def get_candles(sym, count=100):
    try:
        ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
        ws = websocket.create_connection(ws_url, timeout=20)
        ws.send(json.dumps({"authorize": TOKEN}))
        auth = json.loads(ws.recv())
        # Even if auth fails, we can still get candles (public data)
        req = {"ticks_history": sym, "style": "candles", "granularity": 60, "count": count, "end": "latest"}
        ws.send(json.dumps(req))
        resp = json.loads(ws.recv())
        ws.close()
        if 'candles' in resp:
            return resp['candles']
        if 'error' in resp:
            return [{"error": resp['error'].get('message')}]
        return []
    except Exception as e:
        return [{"error": str(e)}]

hunt = st.multiselect("Hunt", ["1HZ100V", "R_100", "R_50", "R_25", "1HZ10V"], default=["1HZ100V", "R_100", "R_50"])
enable = st.checkbox("ENABLE BRAIN")

st.caption(f"Websocket AppID: {APP_ID} (fixed) | OAuth Client: {CLIENT_ID[:8]}...")

if enable:
    st.info(f"🧠 Brain enabled at {datetime.now().strftime('%H:%M:%S')} - Hunting: {', '.join(hunt)}")
    for sym in hunt:
        data = get_candles(sym)
        if data and 'close' in data[0]:
            df = pd.DataFrame(data)
            st.success(f"**{sym}** LIVE - {len(data)} candles - Last: {data[-1]['close']}")
            st.line_chart(df['close'])
        elif data and 'error' in data[0]:
            st.error(f"{sym}: {data[0]['error']}")
        else:
            st.warning(f"{sym} - no data")
else:
    st.write("Tick ENABLE BRAIN")
