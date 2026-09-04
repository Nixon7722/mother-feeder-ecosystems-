import streamlit as st, requests, json, websocket, time, pandas as pd
from datetime import datetime
st.set_page_config(page_title="MOTHER V10 PERFECT", layout="wide")
st.title("MOTHER V10 - PERFECT SAFE")
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
st.sidebar.header("PERFECT SAFE")
sym=st.sidebar.selectbox("Symbol",["1HZ100V","1HZ10V","R_100"],0)
stake=0.5
mult=30
sl=0.5
tp=0.8
interval=120
cooldown=300
auto=st.sidebar.checkbox("ENABLE AUTO SAFE",value=st.session_state.auto)
st.session_state.auto=auto
t1,t2=st.tabs(["SAFE LIVE","PROFIT"])
with t1:
    if st.session_state.auto:
        st.success("PERFECT SAFE RUNNING - Keep tab OPEN!")
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
            prof=ws({"profit_table":1,"description":1,"limit":20,"sort":"DESC"}).get("profit_table",{}).get("transactions",[])
            today_pl=0
            for x in prof[:10]:
                try:
                    today_pl+=float(x.get('sell_price',0) or 0)-float(x.get('buy_price',0) or 0)
                except:
                    pass
            if today_pl <= -3:
                sb.error("DAILY SL HIT - Stopped")
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
                    msg="BUY " + sig + " ID " + str(cid)
                    st.session_state.logs.insert(0,msg)
                    sb.success(msg)
            else:
                tr="UP" if last['e9']>last['e21'] else "DOWN"
                price=str(round(float(last['close']),2))
                sb.write(now + " Trend " + tr + " Price " + price + " Open " + str(oc) + " Today " + str(round(today_pl,2)))
            lb.code("\n".join(st.session_state.logs[:10]))
            cb.line_chart(df[['close','e9','e21']].tail(25))
            time.sleep(interval)
with t2:
    if st.button("Load Profit"):
        r=ws({"profit_table":1,"description":1,"limit":20,"sort":"DESC"})
        tx=r.get("profit_table",{}).get("transactions",[])
        tot=0
        for t in tx[:15]:
            b=float(t.get('buy_price',0) or 0)
            s=float(t.get('sell_price',0) or 0)
            pl=s-b
            tot+=pl
            st.write(str(t.get('contract_id')) + " P/L " + str(round(pl,2)))
        st.metric("Total",str(round(tot,2)))
