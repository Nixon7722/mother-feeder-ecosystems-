import streamlit as st, json, websocket
from datetime import datetime
import pandas as pd

st.set_page_config(page_title='MOTHER V14.4 - LIVE', layout='wide', page_icon='🧠')
st.title('🧠 MOTHER V14.4 - LIVE')

# YOUR IDS
CLIENT_ID = "01a06813-896f-7ee5-934d-6b51adb1d481"
APP_ID = "1089"
TOKEN = st.secrets.get('DERIV_TOKEN', 'pat_6604c2a51cf0555cac31e30bff808ef704d7323e12594625f2e30a389b14e440')

def get_candles(sym, count=100):
    try:
        ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
        ws = websocket.create_connection(ws_url, timeout=15)
        ws.send(json.dumps({"authorize": TOKEN}))
        ws.recv() # auth response
        req = {"ticks_history": sym, "style": "candles", "granularity": 60, "count": count, "end": "latest"}
        ws.send(json.dumps(req))
        resp = json.loads(ws.recv())
        ws.close()
        return resp.get('candles', [])
    except Exception as e:
        return []

# Sidebar
st.sidebar.success(f"AppID: {APP_ID} ✓\nToken: {TOKEN[:12]}... ✓")

hunt = st.multiselect("Hunt", ["1HZ100V", "R_100", "R_50", "R_25", "1HZ10V", "1HZ15V"], default=["1HZ100V", "R_100", "R_50"])
enable = st.checkbox("ENABLE BRAIN", value=True)

st.caption(f"Websocket AppID: {APP_ID} | OAuth Client: {CLIENT_ID[:8]}... | Connected")

if enable:
    st.info(f"🧠 Brain enabled at {datetime.now().strftime('%H:%M:%S')} - Hunting: {', '.join(hunt)}")

    cols = st.columns(len(hunt))
    for i, sym in enumerate(hunt):
        data = get_candles(sym)
        with cols[i] if len(hunt) <= 3 else st.container():
            if data:
                df = pd.DataFrame(data)
                last = data[-1]['close']
                prev = data[-2]['close'] if len(data) > 1 else last
                change = last - prev
                color = "green" if change >= 0 else "red"

                st.markdown(f"""
                <div style="background:{'#0e3d1a' if color=='green' else '#3d0e0e'};padding:12px;border-radius:10px;text-align:center">
                    <b>{sym} LIVE</b><br>Last: {last}<br><span style="color:{color}">{'+' if change>=0 else ''}{change:.2f}</span>
                </div>
                """, unsafe_allow_html=True)

                # BEAUTIFUL ZOOMED CHART - only close price
                chart_df = pd.DataFrame({"close": df['close']})
                st.line_chart(chart_df, height=200)
            else:
                st.warning(f"{sym} connecting...")
else:
    st.write("Tick ENABLE BRAIN")
