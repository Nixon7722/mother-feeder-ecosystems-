import streamlit as st, requests, json, websocket, time, pandas as pd
from datetime import datetime
st.set_page_config(page_title="MOTHER V11 BEAST", layout="wide")
st.title("MOTHER V11 - $20 LOCK + $50 BEAST")

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
        w.send(json.dumps({"ticks_history":sym,"style":"candles","granularity":60,"count":100,"end":"latest"}))
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

def rsi_calc(df, period=14):
    delta=df['close'].diff()
    gain=delta.where(delta>0,0).ewm(alpha=1/period).mean()
    loss=(-delta.where(delta<0,0)).ewm(alpha=1/period).mean()
    rs=gain/loss
    return 100-(100/(1+rs))

st.sidebar.header("BEAST MODE")
sym=st.sidebar.selectbox("Symbol",["1HZ100V","1HZ10V","R_100","BOOM1000"],0)
lock_target=st.sidebar.number_input("Lock Target $",10,30,20)
super_target=st.sidebar.number_input("Super Target $",40,100,50)
base_stake=0.5
auto=st.sidebar.checkbox("ENABLE BEAST",value=st.session_state.auto)
st.session_state.auto=auto

t1,t2=st.tabs(["BEAST LIVE","PROFIT"])
with t1:
    if st.session_state.auto:
        st.success("BEAST RUNNING - Keep OPEN!")
    sb=st.empty()
    lb=st.empty()
    cb=st.empty()
    if st.session_state.auto:
        for _ in range(1000):
            df=candles(sym)
            if df.empty or len(df)<30:
                time.sleep(10)
                continue
            df['e9']=df['close'].ewm(span=9).mean()
            df['e21']=df['close'].ewm(span=21).mean()
            df['rsi']=rsi_calc(df,14)
            last=df.iloc[-1]
            prev=df.iloc[-2]
            port=ws({"portfolio":1}).get("portfolio",{}).get("contracts",[])
            prof=ws({"profit_table":1,"description":1,"limit":100,"sort":"DESC"}).get("profit_table",{}).get("transactions",[])
            total_pl=0
            for x in prof:
                try:
                    total_pl+=float(x.get('sell_price',0) or 0)-float(x.get('buy_price',0) or 0)
                except:
                    pass
            # PHASE LOGIC
            if total_pl < lock_target:
                phase="SAFE LOCK"
                stake=0.5 if total_pl<10 else 0.75 if total_pl<15 else 1.0
                mult=30
                sl=0.5
                tp=0.8
                cooldown=300
                is_beast=False
            else:
                phase="BEAST MODE"
                extra=total_pl-lock_target
                stake=1.0 if extra<10 else 1.5 if extra<20 else 2.0 if extra<30 else 3.0
                mult=60
                sl=1.0
                tp=2.0
                cooldown=90
                is_beast=True
            
            if stake>3.0:
                stake=3.0
            if total_pl <= -5:
                sb.error("MAX LOSS $5 HIT - STOP")
                break
            
            oc=len(port)
            now=datetime.now().strftime("%H:%M:%S")
            ts=time.time()
            can=(ts-st.session_state.lt)>cooldown
            sig=None
            
            if oc==0 and can:
                if not is_beast:
                    # SAFE - CROSS only
                    if prev['e9']<=prev['e21'] and last['e9']>last['e21']:
                        sig="MULTUP"
                    elif prev['e9']>=prev['e21'] and last['e9']<last['e21']:
                        sig="MULTDOWN"
                else:
                    # BEAST - TREND + RSI + Strong reading
                    rsi=float(last['rsi'])
                    ema_diff=abs(float(last['e9'])-float(last['e21']))/float(last['e21'])*100
                    # Only trade if trend strong + RSI not overbought
                    if float(last['e9'])>float(last['e21']) and rsi>55 and rsi<75 and ema_diff>0.05:
                        sig="MULTUP"
                    elif float(last['e9'])<float(last['e21']) and rsi<45 and rsi>25 and ema_diff>0.05:
                        sig="MULTDOWN"
            
            if sig:
                r=buy(sym,stake,mult,sl,tp,sig)
                cid=r.get('buy',{}).get('contract_id','?')
                if cid!='?':
                    st.session_state.lt=ts
                    msg=phase + " " + sig + " Stake $" + str(stake) + " ID " + str(cid)
                    st.session_state.logs.insert(0,msg)
                    sb.success(msg)
            else:
                tr="UP" if float(last['e9'])>float(last['e21']) else "DOWN"
                price=str(round(float(last['close']),2))
                rsi_v=str(round(float(last['rsi']),1))
                sb.write(now + " [" + phase + "] " + tr + " Price " + price + " RSI " + rsi_v + " Stake $" + str(stake) + " Total $" + str(round(total_pl,2)) + " Open " + str(oc))
            
            lb.code("\n".join(st.session_state.logs[:12]))
            cb.line_chart(df[['close','e9','e21']].tail(30))
            time.sleep(cooldown if not sig else 5)

with t2:
    if st.button("Load Profit"):
        r=ws({"profit_table":1,"description":1,"limit":30,"sort":"DESC"})
        tx=r.get("profit_table",{}).get("transactions",[])
        tot=0
        for t in tx:
            try:
                tot+=float(t.get('sell_price',0) or 0)-float(t.get('buy_price',0) or 0)
            except:
                pass
        for t in tx[:15]:
            b=float(t.get('buy_price',0) or 0)
            s=float(t.get('sell_price',0) or 0)
            st.write(str(t.get('contract_id')) + " " + str(round(s-b,2)))
        st.metric("Total",str(round(tot,2)))
        if tot>=20:
            st.success("LOCKED $20 - BEAST ACTIVE - Target $50+")
        else:
            st.write("Need $" + str(round(20-tot,2)) + " more to unlock BEAST")
