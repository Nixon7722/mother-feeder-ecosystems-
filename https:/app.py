import streamlit as st, requests, json, websocket, time, pandas as pd
from datetime import datetime

st.set_page_config(page_title="MOTHER V10 PERFECT", layout="wide")
st.title("🧠 MOTHER V10 - PERFECT SAFE")

TOKEN = st.secrets.get("DERIV_TOKEN","")
APP_ID = st.secrets.get("DERIV_APP_ID","34iR6HMxOfgO6m5LWOrAp")
AID = "DOT94422096"

if "auto" not in st.session_state:
    st.session_state.auto=False
if "logs" not in st.session_state:
    st.session_state.logs=[]
if "lt" not in st.session_state:
    st.session_state.lt=0

def otp_url():
    h={"Authorization":f"Bearer {TOKEN}","Deriv-App-ID":APP_ID}
    r=requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{AID}/otp",headers=h,timeout=20)
    return r.json()["data"]["url"]

def ws(p):
    u=otp_url()
    w=websocket.create_connection(u,timeout=15)
    w.send(json.dumps(p))
    r=json.loads(w.recv())
    w.close()
    return r

def candles(sym):
    try:
        u=otp_url()
        w=websocket.create_connection(u,timeout=15)
        w.send(json.dumps({"ticks_history":sym,"style":"candles","granularity":60,"count":50,"end":"latest"}))
        r=json.loads(w.recv())
        w.close()
        return pd.DataFrame(r.get("candles",[]))
    except:
        return pd.DataFrame()

def buy(sym,stake,mult,sl,tp,typ):
    pr={"proposal":1,"amount":stake,"basis":"stake","contract_type":typ,"currency":"USD","multiplier":mult,"underlying_symbol":sym,"limit_order":{"stop_loss":sl,"take_profit":tp}}
    a=ws(pr)
    if "proposal" in a:
        b=ws({"buy":a["proposal"]["id"],"price":stake})
        return b
    return a

# SETTINGS - PERFECT SAFE
st.sidebar.header("PERFECT SAFE")
sym=st.sidebar.selectbox("Symbol",["1HZ100V","1HZ10V","R_100"],0)
stake=0.5
mult=30
sl=0.5
tp=0.8
st.sidebar.write(f"Stake ${stake} Mult {mult} SL ${sl} TP ${tp}")
st.sidebar.write("Mode: CROSS SAFE + Daily SL $3")
interval=120
cooldown=300
auto=st.sidebar.checkbox("🤖 ENABLE AUTO SAFE",value=st.session_state.auto)
st.session_state.auto=auto

t1,t2=st.tabs(["🛡️ SAFE LIVE","📊 PROFIT"])

with t1:
    if st.session_state.auto:
        st.success("🛡️ PERFECT SAFE RUNNING - 120s - Keep tab OPEN!")
    else:
        st.warning("Enable >> sidebar")
    sb=st.empty()
    lb=st.empty()
    cb=st.empty()
    if st.session_state.auto:
        for _ in range(500):
            df=candles(sym)
            if df.empty:
                time.sleep(10)
                continue
            df['e9']=df['close'].ewm(span=9).mean()
            df['e21']=df['close'].ewm(span=21).mean()
            last=df.iloc[-1]
            prev=df.iloc[-2]
            port=ws({"portfolio":1}).get("portfolio",{}).get("contracts",[])
            # daily loss check
            prof=ws({"profit_table":1,"description":1,"limit":20,"sort":"DESC"}).get("profit_table",{}).get("transactions",[])
            today_pl=sum([float(x.get('sell_price',0) or 0)-float(x.get('buy_price',0) or 0) for x in prof[:10]])
            if today_pl <= -3:
                sb.error(f"🛑 DAILY SL HIT ${today_pl:.2f} - Stopped for today")
                break
            oc=len(port)
            now=datetime.now().strftime("%H:%M:%S")
            ts=time.time()
            can=(ts-st.session_state.lt)>cooldown
            sig=None
            if oc==0 and can:
                if prev['e9']<=prev['e21'] and last['e9']>last['e21']:
                    sig="MULTUP"
                elif prev['e9']>=prev['e21'] and last['e9']<last['e21']:
                    sig="MULTDOWN"
            if sig:
                r=buy(sym,stake,mult,sl,tp,sig)
                cid=r.get('buy',{}).get('contract_id','?')
                if cid!='?':
                    st.session_state.lt=ts
                    msg=f"✅ {now} {sig} ID {cid} Price {last['close']:.2f}"
                    st.session_state.logs.insert(0,msg)
                    sb.success(msg)
            else:
                tr="UP" if last['e9']>last['e21'] else "DOWN"
                sb.write(f"{now} Trend {tr} | {last['close']:.2f} | Open {oc} | Today {today_pl:.2f} |
