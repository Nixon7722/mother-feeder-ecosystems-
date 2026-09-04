import streamlit as st, requests, json, websocket, time, pandas as pd
from datetime import datetime
st.set_page_config(page_title="MOTHER V13 HUNTER", layout="wide")
st.title("MOTHER V13 HUNTER $20/$50")
TOKEN = st.secrets.get("DERIV_TOKEN","")
APP_ID = st.secrets.get("DERIV_APP_ID","34iR6HMxOfgO6m5LWOrAp")
AID = "DOT94422096"
if "auto" not in st.session_state:
    st.session_state.auto=False
if "logs" not in st.session_state:
    st.session_state.logs=[]
if "lt" not in st.session_state:
    st.session_state.lt=0
if "trade_memory" not in st.session_state:
    st.session_state.trade_memory=[]
if "loss_streak" not in st.session_state:
    st.session_state.loss_streak=0
if "win_streak" not in st.session_state:
    st.session_state.win_streak=0

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
        w.send(json.dumps({"ticks_history":sym,"style":"candles","granularity":60,"count":120,"end":"latest"}))
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
def predict_win_prob(rsi, ema_diff):
    mem=st.session_state.trade_memory
    if len(mem)<10:
        return 0.62
    sim=[m for m in mem if abs(m['rsi']-rsi)<6 and abs(m['ema_diff']-ema_diff)<0.12]
    if len(sim)<5:
        sim=mem[-20:]
    wins=sum(1 for s in sim if s['result']=='WIN')
    return wins/len(sim) if sim else 0.55

st.sidebar.header("V13 HUNTER")
HUNT_LIST=["1HZ100V","R_100","R_50","BOOM1000","CRASH1000"]
selected=st.sidebar.multiselect("Hunt Symbols",HUNT_LIST, default=HUNT_LIST[:4])
auto=st.sidebar.checkbox("ENABLE HUNTER",value=st.session_state.auto)
st.session_state.auto=auto
st.sidebar.write("Memory: " + str(len(st.session_state.trade_memory)))

t1,t2=st.tabs(["HUNTER LIVE","MEMORY"])
with t1:
    if st.session_state.auto:
        st.success("HUNTER SCANNING " + str(len(selected)) + " MARKETS")
    sb=st.empty()
    scan_box=st.empty()
    lb=st.empty()
    cb=st.empty()
    if st.session_state.auto:
        for _ in range(5000):
            prof=ws({"profit_table":1,"description":1,"limit":25,"sort":"DESC"}).get("profit_table",{}).get("transactions",[])
            total_pl=0
            for x in prof:
                try:
                    total_pl+=float(x.get('sell_price',0) or 0)-float(x.get('buy_price',0) or 0)
                except:
                    pass
            for t in prof[:5]:
                cid=str(t.get('contract_id'))
                if not any(m.get('id')==cid for m in st.session_state.trade_memory) and t.get('sell_price'):
                    pl=float(t.get('sell_price',0) or 0)-float(t.get('buy_price',0) or 0)
                    res='WIN' if pl>0 else 'LOSS'
                    st.session_state.trade_memory.append({'id':cid,'rsi':50,'ema_diff':0.1,'result':res,'profit':pl})
                    if res=='WIN':
                        st.session_state.win_streak+=1
                        st.session_state.loss_streak=0
                    else:
                        st.session_state.loss_streak+=1
                        st.session_state.win_streak=0
            port=ws({"portfolio":1}).get("portfolio",{}).get("contracts",[])
            oc=len(port)
            best_trade=None
            best_prob=0
            scan_text=""
            for sym in selected:
                df=candles(sym)
                if df.empty or len(df)<40:
                    continue
                df['e9']=df['close'].ewm(span=9).mean()
                df['e21']=df['close'].ewm(span=21).mean()
                df['e50']=df['close'].ewm(span=50).mean()
                df['rsi']=rsi_calc(df,14)
                last=df.iloc[-1]
                rsi_v=float(last['rsi'])
                ema_diff_v=float(abs(float(last['e9'])-float(last['e21']))/float(last['e21'])*100)
                prob=predict_win_prob(rsi_v, ema_diff_v)
                sig=None
                if float(last['e9'])>float(last['e21']) and float(last['e9'])>float(last['e50']) and 55<rsi_v<72 and ema_diff_v>0.07:
                    sig="MULTUP"
                elif float(last['e9'])<float(last['e21']) and float(last['e9'])<float(last['e50']) and 28<rsi_v<45 and ema_diff_v>0.07:
                    sig="MULTDOWN"
                tr="UP" if float(last['e9'])>float(last['e21']) else "DOWN"
                scan_text+=sym + " " + tr + " RSI " + str(int(rsi_v)) + " Prob " + str(int(prob*100)) + "% " + (sig or "WAIT") + " | "
                if sig and prob>best_prob and prob>=0.62:
                    best_prob=prob
                    best_trade={'sym':sym,'sig':sig,'rsi':rsi_v,'ema_diff':ema_diff_v,'prob':prob,'df':df}
            scan_box.info("SCANNING: " + scan_text)
            if st.session_state.loss_streak>=2:
                cooldown=900
                stake=0.5
                mode="PAUSE"
            elif st.session_state.win_streak>=4 and best_prob>0.70:
                cooldown=60
                stake=3.0 if total_pl>20 else 2.0
                mode="BEAST FEED"
            elif total_pl>=20:
                cooldown=90
                stake=1.5
                mode="AGGRESSIVE"
            else:
                cooldown=120
                stake=0.5 if total_pl<10 else 0.75
                mode="SAFE"
            ts=time.time()
            can=(ts-st.session_state.lt)>cooldown
            if best_trade and oc==0 and can:
                bt=best_trade
                sl=0.6
                tp=1.3 if mode=="SAFE" else 2.5
                if mode=="BEAST FEED":
                    tp=3.5
                r=buy(bt['sym'],stake,50,sl,tp,bt['sig'])
                cid=r.get('buy',{}).get('contract_id','?')
                if cid!='?':
                    st.session_state.lt=ts
                    msg=mode + " " + bt['sym'] + " " + bt['sig'] + " $" + str(stake) + " Prob " + str(int(bt['prob']*100)) + "% ID " + str(cid)
                    st.session_state.logs.insert(0,msg)
                    sb.success(msg)
            else:
                now=datetime.now().strftime("%H:%M:%S")
                if best_trade:
                    sb.write(now + " [" + mode + "] BEST " + best_trade['sym'] + " " + best_trade['sig'] + " Prob " + str(int(best_prob*100)) + "% Stake $" + str(stake) + " Total $" + str(round(total_pl,2)))
                else:
                    sb.write(now + " [" + mode + "] No setup Total $" + str(round(total_pl,2)) + " Mem " + str(len(st.session_state.trade_memory)))
            lb.code("\n".join(st.session_state.logs[:12]))
            if best_trade:
                cb.line_chart(best_trade['df'][['close','e9','e21']].tail(40))
            time.sleep(15)
with t2:
    if st.button("Load Profit"):
        r=ws({"profit_table":1,"description":1,"limit":20,"sort":"DESC"})
        tx=r.get("profit_table",{}).get("transactions",[])
        tot=0
        for t in tx:
            try:
                tot+=float(t.get('sell_price',0) or 0)-float(t.get('buy_price',0) or 0)
            except:
                pass
        st.metric("Total",str(round(tot,2)))
