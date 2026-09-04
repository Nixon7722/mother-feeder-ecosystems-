import streamlit as st, requests, json, websocket, time, pandas as pd
from datetime import datetime
import math

st.set_page_config(page_title="MOTHER V12 MEMORY", layout="wide")
st.title("🧠 MOTHER V12 - MEMORY AI PREDICTOR")

TOKEN = st.secrets.get("DERIV_TOKEN","")
APP_ID = st.secrets.get("DERIV_APP_ID","34iR6HMxOfgO6m5LWOrAp")
AID = "DOT94422096"

# MEMORY - NEVER FORGETS
if "auto" not in st.session_state:
    st.session_state.auto=False
if "logs" not in st.session_state:
    st.session_state.logs=[]
if "lt" not in st.session_state:
    st.session_state.lt=0
if "trade_memory" not in st.session_state:
    st.session_state.trade_memory=[] # [{rsi, ema_diff, hour, result, profit}]
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
        w.send(json.dumps({"ticks_history":sym,"style":"candles","granularity":60,"count":150,"end":"latest"}))
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
def atr_calc(df, period=14):
    hl=df['high']-df['low']
    hc=(df['high']-df['close'].shift()).abs()
    lc=(df['low']-df['close'].shift()).abs()
    tr=pd.concat([hl,hc,lc],axis=1).max(axis=1)
    return tr.ewm(alpha=1/period).mean()

# PREDICTOR - USES HISTORY
def predict_win_prob(current_rsi, ema_diff, hour):
    mem=st.session_state.trade_memory
    if len(mem)<10:
        return 0.6 # no history yet, default 60%
    # Find similar past trades
    similar=[m for m in mem if abs(m['rsi']-current_rsi)<5 and abs(m['ema_diff']-ema_diff)<0.1]
    if len(similar)<5:
        similar=mem[-20:] # use recent 20
    wins=sum(1 for s in similar if s['result']=='WIN')
    prob=wins/len(similar) if similar else 0.5
    return prob

st.sidebar.header("V12 MEMORY AI")
sym=st.sidebar.selectbox("Symbol",["1HZ100V","1HZ10V","R_100","R_50"],0)
base=0.5
auto=st.sidebar.checkbox("🧠 ENABLE MOTHER AI",value=st.session_state.auto)
st.session_state.auto=auto
st.sidebar.write("Memory: " + str(len(st.session_state.trade_memory)) + " trades")
st.sidebar.write("Win streak: " + str(st.session_state.win_streak) + " Loss streak: " + str(st.session_state.loss_streak))

t1,t2=st.tabs(["MOTHER LIVE","MEMORY BRAIN"])
with t1:
    if st.session_state.auto:
        st.success("MOTHER AI WATCHING - Full aggressive on good day!")
    sb=st.empty()
    lb=st.empty()
    cb=st.empty()
    mem_box=st.empty()
    if st.session_state.auto:
        for _ in range(2000):
            df=candles(sym)
            if df.empty or len(df)<50:
                time.sleep(10)
                continue
            df['e9']=df['close'].ewm(span=9).mean()
            df['e21']=df['close'].ewm(span=21).mean()
            df['e50']=df['close'].ewm(span=50).mean()
            df['rsi']=rsi_calc(df,14)
            df['atr']=atr_calc(df,14)
            df['vol']=df['close'].pct_change().rolling(20).std()
            last=df.iloc[-1]
            prev=df.iloc[-2]
            
            # GET PROFIT + UPDATE MEMORY FROM DERIV
            prof=ws({"profit_table":1,"description":1,"limit":30,"sort":"DESC"}).get("profit_table",{}).get("transactions",[])
            total_pl=0
            for x in prof:
                try:
                    total_pl+=float(x.get('sell_price',0) or 0)-float(x.get('buy_price',0) or 0)
                except:
                    pass
            # Update memory with latest closed trades
            for t in prof[:5]:
                cid=str(t.get('contract_id'))
                already=any(m.get('id')==cid for m in st.session_state.trade_memory)
                if not already and t.get('sell_price'):
                    pl=float(t.get('sell_price',0) or 0)-float(t.get('buy_price',0) or 0)
                    res='WIN' if pl>0 else 'LOSS'
                    st.session_state.trade_memory.append({
                        'id':cid,'rsi':float(last['rsi']),'ema_diff':float(abs(float(last['e9'])-float(last['e21']))/float(last['e21'])*100),
                        'result':res,'profit':pl,'hour':datetime.now().hour
                    })
                    if res=='WIN':
                        st.session_state.win_streak+=1
                        st.session_state.loss_streak=0
                    else:
                        st.session_state.loss_streak+=1
                        st.session_state.win_streak=0
                    if len(st.session_state.trade_memory)>200:
                        st.session_state.trade_memory=st.session_state.trade_memory[-200:]
            
            port=ws({"portfolio":1}).get("portfolio",{}).get("contracts",[])
            oc=len(port)
            now=datetime.now().strftime("%H:%M:%S")
            ts=time.time()
            
            # BRAIN DECISIONS
            rsi_v=float(last['rsi'])
            ema_diff_v=float(abs(float(last['e9'])-float(last['e21']))/float(last['e21'])*100)
            atr_v=float(last['atr'])
            vol_v=float(last['vol']*100) if not pd.isna(last['vol']) else 0
            win_prob=predict_win_prob(rsi_v, ema_diff_v, datetime.now().hour)
            
            # LOWEST LOSS LOGIC
            if st.session_state.loss_streak>=2:
                cooldown=900 # pause 15 min after 2 losses
                stake=0.5
                mode="RECOVERY PAUSE"
            elif st.session_state.win_streak>=4 and win_prob>0.7:
                # BEAST FEED MODE - good day!
                cooldown=60
                stake=3.0 if total_pl>20 else 2.0
                mode="BEAST FEED 🔥"
            elif total_pl>=20:
                cooldown=90
                stake=1.5 if win_prob>0.65 else 1.0
                mode="AGGRESSIVE"
            else:
                cooldown=180
                stake=0.5 if total_pl<10 else 0.75
                mode="SAFE"
            
            if stake>3.0:
                stake=3.0
            can=(ts-st.session_state.lt)>cooldown
            if total_pl<=-5:
                sb.error("MAX LOSS $5 - MOTHER STOPPED TO PROTECT")
                break
            
            sig=None
            conf=0
            if oc==0 and can and win_prob>=0.60: # Only trade if brain says >60% win chance
                # Triple confirmation
                trend_up=float(last['e9'])>float(last['e21']) and float(last['e9'])>float(last['e50'])
                trend_down=float(last['e9'])<float(last['e21']) and float(last['e9'])<float(last['e50'])
                strong_trend=ema_diff_v>0.08
                good_vol=vol_v<0.5 # avoid crazy volatility
                
                if trend_up and 55<rsi_v<72 and strong_trend and good_vol:
                    sig="MULTUP"
                    conf=win_prob*100
                elif trend_down and 28<rsi_v<45 and strong_trend and good_vol:
                    sig="MULTDOWN"
                    conf=win_prob*100
            
            if sig:
                # Dynamic SL/TP based on ATR
                sl_val=max(0.5, round(atr_v*2,1))
                tp_val=round(sl_val*2.2,1) # 2.2 RR
                if mode=="BEAST FEED 🔥":
                    tp_val=round(sl_val*3,1)
                r=buy(sym,stake,50,sl_val,tp_val,sig)
                cid=r.get('buy',{}).get('contract_id','?')
                if cid!='?':
                    st.session_state.lt=ts
                    msg=mode + " " + sig + " $" + str(stake) + " Conf " + str(int(conf)) + "% ID " + str(cid)
                    st.session_state.logs.insert(0,msg)
                    sb.success(msg)
            else:
                tr="UP" if float(last['e9'])>float(last['e21']) else "DOWN"
                sb.write(now + " [" + mode + "] Trend " + tr + " RSI " + str(round(rsi_v,1)) + " Prob " + str(int(win_prob*100)) + "% Stake $" + str(stake) + " Total $" + str(round(total_pl,2)) + " Vol " + str(round(vol_v,3)) + "%")
            
            lb.code("\n".join(st.session_state.logs[:10]))
            mem_box.write("🧠 Brain memory: " + str(len(st.session_state.trade_memory)) + " | WinProb " + str(int(win_prob*100)) + "% | LossStreak " + str(st.session_state.loss_streak) + " | WinStreak " + str(st.session_state.win_streak))
            cb.line_chart(df[['close','e9','e21']].tail(40))
            time.sleep(20 if not sig else 5)

with t2:
    if st.button("Load Profit + Memory"):
        r=ws({"profit_table":1,"description":1,"limit":30,"sort":"DESC"})
        tx=r.get("profit_table",{}).get("transactions",[])
        tot=0
        for t in tx:
            try:
                tot+=float(t.get('sell_price',0) or 0)-float(t.get('buy_price',0) or 0)
            except:
                pass
        st.metric("Total P/L",str(round(tot,2)))
        st.write("Memory Brain:")
        for m in st.session_state.trade_memory[-15:][::-1]:
            c="🟢" if m['result']=='WIN' else "🔴"
            st.write(c + " RSI " + str(round(m['rsi'],1)) + " " + m['result'] + " $" + str(round(m['profit'],2)))
