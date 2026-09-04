import streamlit as st, requests, json, websocket, time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MOTHER V10 AUTO", layout="wide")
st.title("🧠 MOTHER V10 - AUTO BRAIN")

TOKEN = st.secrets.get("DERIV_TOKEN", "")
APP_ID = st.secrets.get("DERIV_APP_ID", "34iR6HMxOfgO6m5LWOrAp")
ACCOUNT_ID = "DOT94422096"

if "auto_on" not in st.session_state:
    st.session_state.auto_on = False
if "logs" not in st.session_state:
    st.session_state.logs = []

def get_otp():
    headers = {"Authorization": f"Bearer {TOKEN}", "Deriv-App-ID": APP_ID}
    r = requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{ACCOUNT_ID}/otp", headers=headers, timeout=20)
    return r.json()["data"]["url"]

def ws_req(payload):
    otp = get_otp()
    ws = websocket.create_connection(otp, timeout=15)
    ws.send(json.dumps(payload))
    resp = json.loads(ws.recv())
    ws.close()
    return resp

def get_candles(symbol="1HZ100V", count=50):
    try:
        otp = get_otp()
        ws = websocket.create_connection(otp, timeout=15)
        ws.send(json.dumps({"ticks_history": symbol, "style": "candles", "granularity": 60, "count": count, "end": "latest"}))
        resp = json.loads(ws.recv())
        ws.close()
        candles = resp.get("candles", [])
        return pd.DataFrame(candles)
    except Exception as e:
        return pd.DataFrame()

def buy_trade(symbol, stake, mult, sl, tp, direction="MULTUP"):
    prop = {"proposal":1,"amount":stake,"basis":"stake","contract_type":direction,"currency":"USD","multiplier":mult,"underlying_symbol":symbol,"limit_order":{"stop_loss":sl,"take_profit":tp}}
    r1 = ws_req(prop)
    if "proposal" in r1:
        r2 = ws_req({"buy": r1["proposal"]["id"], "price": stake})
        return r2
    return r1

# --- CONTROLS ---
st.sidebar.header("⚙️ AUTO SETTINGS")
symbol = st.sidebar.selectbox("Symbol", ["1HZ100V","1HZ10V","R_100","R_50"], index=0)
stake = st.sidebar.number_input("Stake $", 0.5, 10.0, 1.0)
mult = st.sidebar.number_input("Multiplier", 10, 1000, 40)
sl = st.sidebar.number_input("SL $", 0.2, 5.0, 0.5)
tp = st.sidebar.number_input("TP $", 0.2, 5.0, 0.8)
interval = st.sidebar.number_input("Check every (sec)", 30, 300, 120)

st.sidebar.divider()
auto = st.sidebar.checkbox("🤖 ENABLE AUTO TRADE", value=st.session_state.auto_on)
st.session_state.auto_on = auto

tab1, tab2, tab3 = st.tabs(["🤖 AUTO LIVE", "📊 PROFIT", "📈 OPEN"])

with tab1:
    st.info(f"Strategy: EMA 9 > EMA 21 = BUY UP | EMA 9 < EMA 21 = BUY DOWN | Symbol: {symbol}")
    log_box = st.empty()
    chart_box = st.empty()
    
    if st.button("🔍 SCAN NOW"):
        df = get_candles(symbol, 50)
        if not df.empty:
            df['ema9'] = df['close'].ewm(span=9).mean()
            df['ema21'] = df['close'].ewm(span=21).mean()
            last = df.iloc[-1]
            st.write(f"Price: {last['close']} | EMA9: {last['ema9']:.2f} | EMA21: {last['ema21']:.2f}")
            chart_box.line_chart(df[['close','ema9','ema21']].tail(30))
            if last['ema9'] > last['ema21']:
                st.success("SIGNAL: UP TREND -> Should BUY MULTUP")
            else:
                st.error("SIGNAL: DOWN TREND -> Should BUY MULTDOWN")
        else:
            st.error("No candles - check API")

    if st.session_state.auto_on:
        st.warning(f"🤖 AUTO RUNNING - Checks every {interval}s - Keep this tab open!")
        status = st.empty()
        for i in range(100):  # run 100 cycles
            if not st.session_state.auto_on:
                break
            df = get_candles(symbol, 50)
            if df.empty:
                status.write("Waiting candles...")
                time.sleep(10)
                continue
            df['ema9'] = df['close'].ewm(span=9).mean()
            df['ema21'] = df['close'].ewm(span=21).mean()
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Check open positions - don't open if already have 1 open
            port = ws_req({"portfolio":1})
            open_count = len(port.get("portfolio",{}).get("contracts",[]))
            
            signal = None
            # Cross detection
            if prev['ema9'] <= prev['ema21'] and last['ema9'] > last['ema21'] and open_count==0:
                signal = "MULTUP"
            elif prev['ema9'] >= prev['ema21'] and last['ema9'] < last['ema21'] and open_count==0:
                signal = "MULTDOWN"
            
            now = datetime.now().strftime("%H:%M:%S")
            if signal:
                res = buy_trade(symbol, stake, mult, sl, tp, signal)
                cid = res.get('buy',{}).get('contract_id','?')
                msg = f"{now} - {signal} - ID {cid} - Open: {open_count}"
                st.session_state.logs.append(msg)
                status.success(msg)
            else:
                status.write(f"{now} - No signal | Price {last['close']} | EMA9 {last['ema9']:.1f} EMA21 {last['ema21']:.1f} | Open: {open_count}")
            
            log_box.write("\n".join(st.session_state.logs[-10:][::-1]))
            chart_box.line_chart(df[['close','ema9','ema21']].tail(30))
            time.sleep(interval)
    else:
        st.write("Enable AUTO in sidebar to start")

with tab2:
    if st.button("Load Profit Table V10"):
        resp = ws_req({"profit_table":1,"description":1,"limit":20,"sort":"DESC"})
        tx = resp.get("profit_table",{}).get("transactions",[])
        for t in tx[:10]:
            buy = t.get('buy_price',0)
            sell = t.get('sell_price',0)
            pl = sell - buy if sell and buy else 0
            color = "🟢" if pl>0 else "🔴"
            st.write(f"{color} ID {t.get('contract_id')} | ${buy} -> ${sell} | P/L ${pl:.2f}")
        if tx:
            df = pd.DataFrame(tx)
            try:
                df['pl'] = df['sell_price'].astype(float) - df['buy_price'].astype(float)
                st.metric("Total 20 trades P/L", f"${df['pl'].sum():.2f}")
            except:
                pass

with tab3:
    if st.button("Load Open"):
        resp = ws_req({"portfolio":1})
        cons = resp.get("portfolio",{}).get("contracts",[])
        for c in cons:
            st.code(f"ID {c.get('contract_id')} | {c.get('underlying_symbol')} | Buy ${c.get('buy_price')} | {c.get('contract_type')} | P/L {c.get('profit_loss')}")
        if cons and st.button("🔴 CLOSE ALL"):
            for c in cons:
                r = ws_req({"sell": c["contract_id"], "price": 0})
                st.write(f"Closed {c['contract_id']}: {r.get('sell',{}).get('sold_for')}")
