import streamlit as st, json, websocket
from datetime import datetime
import pandas as pd
import altair as alt

st.set_page_config(page_title='MOTHER V14.4 - LIVE', layout='wide', page_icon='🧠')
st.title('🧠 MOTHER V14.4 - LIVE')

APP_ID = "1089"
TOKEN = st.secrets.get('DERIV_TOKEN', 'pat_6604c2a51cf0555cac31e30bff808ef704d7323e12594625f2e30a389b14e440')

def get_candles(sym, count=100):
    try:
        ws = websocket.create_connection(f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}", timeout=15)
        ws.send(json.dumps({"authorize": TOKEN}))
        ws.recv()
        ws.send(json.dumps({"ticks_history": sym, "style": "candles", "granularity": 60, "count": count, "end": "latest"}))
        resp = json.loads(ws.recv())
        ws.close()
        return resp.get('candles', [])
    except:
        return []

hunt = st.multiselect("Hunt", ["1HZ100V", "R_100", "R_50", "R_25", "1HZ10V", "1HZ15V"], default=["1HZ100V", "R_100", "R_50"])
enable = st.checkbox("ENABLE BRAIN", value=True)

if enable:
    st.success(f"🧠 Brain hunting {', '.join(hunt)} at {datetime.now().strftime('%H:%M:%S')}")

    for sym in hunt:
        data = get_candles(sym)
        if data:
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'])
            last = df['close'].iloc[-1]
            prev = df['close'].iloc[-2]
            diff = last - prev
            is_up = diff >= 0

            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"""
                <div style="background:{'#0f3d15' if is_up else '#3d0f0f'};padding:15px;border-radius:12px;text-align:center;margin-top:20px">
                    <b style="font-size:18px">{sym}</b><br>
                    <span style="font-size:22px;font-weight:bold">{last:.2f}</span><br>
                    <span style="color:{'#00ff88' if is_up else '#ff4444'}">{'+' if is_up else ''}{diff:.2f}</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                # PERFECT ZOOMED CHART
                chart = alt.Chart(df.reset_index()).mark_line(color='#00ff88' if is_up else '#ff4444', strokeWidth=3).encode(
                    x=alt.X('index:Q', title='Candle'),
                    y=alt.Y('close:Q', title='Price', scale=alt.Scale(zero=False)),
                    tooltip=['close']
                ).properties(height=200).interactive()
                st.altair_chart(chart, use_container_width=True)
            st.divider()
        else:
            st.warning(f"{sym} connecting...")
else:
    st.write("Enable brain")
