import streamlit as st, requests, json, websocket
from datetime import datetime
import pandas as pd

st.set_page_config(page_title='MOTHER V14.4 - FIXED', layout='wide')
st.title('MOTHER V14.4 - FIXED')

# Secrets
TOKEN = st.secrets.get('DERIV_TOKEN', '')
APP_ID = st.secrets.get('DERIV_APP_ID', '3416')
AID = 'DOT9442096'

def otp_url():
    if not TOKEN:
        return None
    h = {'Authorization': f'Bearer {TOKEN}', 'Deriv-App-Id': APP_ID}
    u = f'https://api.derivws.com/trading/v1/options/login'
    try:
        r = requests.post(u, headers=h, timeout=20)
        if r.status_code != 200 or not r.text:
            return None
        j = r.json()
        return j.get('data', {}).get('url')
    except:
        return None

def ws_req(payload):
    try:
        url = otp_url()
        if not url:
            return {}
        w = websocket.create_connection(url, timeout=15)
        w.send(json.dumps(payload))
        resp = w.recv()
        w.close()
        return json.loads(resp)
    except Exception as e:
        return {"error": str(e)}

def candles(sym):
    try:
        m = {'ticks_history': sym, 'style': 'candles', 'granularity': 60, 'count': 100, 'end': 'latest'}
        r = ws_req(m)
        if 'candles' in r:
            return r['candles']
        return []
    except:
        return []

# UI
hunt = st.multiselect("Hunt", ["1HZ100V", "R_100", "R_50", "R_25", "1HZ10V"], default=["1HZ100V", "R_100", "R_50"])
enable = st.checkbox("ENABLE BRAIN")

if not TOKEN:
    st.warning("⚠️ Add DERIV_TOKEN in Streamlit Secrets: Manage app > Settings > Secrets")
    st.code('DERIV_TOKEN = "your_token"\nDERIV_APP_ID = "3416"', language='toml')
else:
    st.success(f"Token loaded...{TOKEN[:4]}**** | AppID: {APP_ID}")

if enable:
    if not TOKEN:
        st.error("Cannot enable brain - token missing!")
    else:
        st.info(f"🧠 Brain enabled at {datetime.now().strftime('%H:%M:%S')} - Hunting: {', '.join(hunt)}")
        for sym in hunt:
            data = candles(sym)
            if data:
                df = pd.DataFrame(data)
                st.write(f"**{sym}** - {len(data)} candles")
                st.line_chart(df['close'] if 'close' in df.columns else df)
            else:
                st.write(f"**{sym}** - waiting data... (API may be slow)")
else:
    st.write("Tick ENABLE BRAIN to start hunting...")
