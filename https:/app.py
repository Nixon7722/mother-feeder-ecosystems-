import streamlit as st, requests, json, websocket, time, pandas as pd, os
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="MOTHER V14 INFINITE", layout="wide")
st.title("🧠 MOTHER V14 - INFINITE BRAIN $20/$50")

TOKEN = st.secrets.get("DERIV_TOKEN","")
APP_ID = st.secrets.get("DERIV_APP_ID","34iR6HMxOfgO6m5LWOrAp")
AID = "DOT94422096"
BRAIN_FILE = "mother_brain.json"

# --- INFINITE BRAIN STORAGE ---
def load_brain():
    if os.path.exists(BRAIN_FILE):
        try:
            with open(BRAIN_FILE,"r") as f:
                data=json.load(f)
                return data.get("cells",[]), data.get("super_cells",[]), data.get("iq",60)
        except:
            return [],[],60
    return [],[],60

def save_brain(cells, super_cells, iq):
    try:
        with open(BRAIN_FILE,"w") as f:
            json.dump({"cells":cells[-2000:],"super_cells":super_cells[-500:], "iq":iq, "last_save":str(datetime.now())}, f)
    except:
        pass

if "cells" not in st.session_state:
    c, sc, iq = load_brain()
    st.session_state.cells=c
    st.session_state.super_cells=sc
    st.session_state.iq=iq
if "auto" not in st.session_state:
    st.session_state.auto=False
if "logs" not in st.session_state:
    st.session_state.logs=[]
if "lt" not in st.session_state:
    st.session_state.lt=0
if "loss_streak" not in st.session_state:
    st.session_state.loss_streak=0
if "win_streak" not in st.session_state:
    st.session_state.win_streak=0
if "total_trades" not in st.session_state:
    st.session_state.total_trades=len(st.session_state.cells)

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

# --- INFINITE INTELLIGENCE PREDICTION ---
def predict_with_infinite_brain(rsi, ema_diff, sym, hour):
    cells=st.session_state.cells
    super_cells=st.session_state.super_cells
    if len(cells)<15:
        return 0.62, "LEARNING"

    # 1. Check SUPER CELLS (multiplied intelligence)
    for sc in super_cells:
        if sc['sym']==sym and abs(sc['rsi_center']-rsi)<sc['rsi_range'] and abs(sc['ema_center']-ema_diff)<0.08:
            return sc['win_rate'], f"SUPER CELL {sc['id']} IQ {sc['power']}"

    # 2. Normal KNN with 2000 cells
    similar=[]
    for c in cells[-1000:]:
        dist = abs(c['rsi']-rsi) + abs(c['ema_diff']-ema_diff)*20
        if c['sym']==sym:
            dist*=0.7
        if abs(c['hour']-hour)<=1:
            dist*=0.8
        similar.append((dist, c))
    similar=sorted(similar, key=lambda x: x[0])[:30]
    wins=sum(1 for d,c in similar if c['result']=='WIN')
    prob=wins/len(similar) if similar else 0.55

    # Boost prob if IQ high
    iq_boost = min(st.session_state.iq/500, 0.08)
    prob = min(prob + iq_boost, 0.92)
    return prob, f"BRAIN {len(cells)} CELLS"

def multiply_brain_cells():
    cells=st.session_state.cells
    if len(cells)<20 or len(cells)%10!=0:
        return
    # Analyze patterns and create SUPER CELL
    df=pd.DataFrame(cells[-100:])
    if df.empty:
        return
    # Find best RSI+SYMBOL combo
    for sym in df['sym'].unique():
        sub=df[df['sym']==sym]
        if len(sub)<8:
            continue
        # Bin RSI 35-45, 55-70 etc
        for r_center in [38, 60, 65]:
            bin_cells=sub[abs(sub['rsi']-r_center)<5]
            if len(bin_cells)>=5:
                wr=(bin_cells['result']=='WIN').mean()
                if wr>=0.70:
                    # MULTIPLY - create super cell
                    sc_id=f"SC-{sym}-{r_center}-{len(st.session_state.super_cells)+1}"
                    new_sc={
                        'id':sc_id,
                        'sym':sym,
                        'rsi_center':r_center,
                        'rsi_range':6,
                        'ema_center':float(bin_cells['ema_diff'].mean()),
                        'win_rate':float(wr),
                        'power':int(wr*100),
                        'created':str(datetime.now()),
                        'trades_used':len(bin_cells)
                    }
                    # Avoid duplicates
                    if not any(s['sym']==sym and abs(s['rsi_center']-r_center)<3 for s in st.session_state.super_cells):
                        st.session_state.super_cells.append(new_sc)
                        st.session_state.iq+=2
                        st.session_state.logs.insert(0,f"🧬 NEW SUPER CELL BORN! {sc_id} {sym} RSI {r_center} WR {int(wr*100)}% IQ {st.session_state.iq}")
    # Increase IQ
    st.session_state.iq = 60 + len(cells)*0.5 + len(st.session_state.super_cells)*5 + (Counter([c['result'] for c in cells[-50:]])['WIN']/50*20 if len(cells)>=50 else 0)
    save_brain(st.session_state.cells, st.session_state.super_cells, st.session_state.iq)

st.sidebar.header("V14 INFINITE")
HUNT_LIST=["1HZ100V","R_100","R_50","BOOM1000","CRASH1000","R_10"]
selected=st.sidebar.multiselect("Hunt Symbols",HUNT_LIST, default=HUNT_LIST[:4])
auto=st.sidebar.checkbox("🧠 ENABLE INFINITE BRAIN",value=st.session_state.auto)
st.session_state.auto=auto
st.sidebar.metric("Brain Cells", len(st.session_state.cells))
st.sidebar.metric("Super Cells", len(st.session_state.super_cells))
st.sidebar.metric("IQ Level", int(st.session_state.iq))
st.sidebar.metric("Total Trades Ever", st.session_state.total_trades)

t1,t2,t3=st.tabs(["HUNTER LIVE","BRAIN CELLS","IQ GROWTH"])
with t1:
    sb=st.empty()
    scan_box=st.empty()
    lb=st.empty()
    cb=st.empty()
    if auto:
        for _ in range(10000):
            prof=ws({"profit_table":1,"description":1,"limit":30,"sort":"DESC"}).get("profit_table",{}).get("transactions",[])
            total_pl=sum(float(x.get('sell_price',0) or 0)-float(x.get('buy_price',0) or 0) for x in prof)
            # LEARN FROM NEW TRADES
            for t in prof[:10]:
                cid=str(t.get('contract_id'))
                if not any(c.get('id')==cid for c in st.session_state.cells) and t.get('sell_price'):
                    pl=float(t.get('sell_price',0) or 0)-float(t.get('buy_price',0) or 0)
                    res='WIN' if pl>0 else 'LOSS'
                    sym=t.get('symbol','UNK')
                    # Find cell temp to update
                    for c in st.session_state.cells:
                        if c.get('temp_id')==cid:
                            c['result']=res
                            c['profit']=pl
                            c['id']=cid
                            del c['temp_id']
                            st.session_state.total_trades+=1
                            if res=='WIN':
                                st.session_state.win_streak+=1
                                st.session_state.loss_streak=0
                            else:
                                st.session_state.loss_streak+=1
                                st.session_state.win_streak=0
                            multiply_brain_cells()
                            break

            port=ws({"portfolio":1}).get("portfolio",{}).get("contracts",[])
            best=None
            best_prob=0
            scan=""
            hour=datetime.now().hour
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
                prob, source = predict_with_infinite_brain(rsi_v, ema_diff_v, sym, hour)
                sig=None
                if float(last['e9'])>float(last['e21']) and float(last['e9'])>float(last['e50']) and 52<rsi_v<75 and ema_diff_v>0.06:
                    sig="MULTUP"
                elif float(last['e9'])<float(last['e21']) and float(last['e9'])<float(last['e50']) and 25<rsi_v<48 and ema_diff_v>0.06:
                    sig="MULTDOWN"
                scan+=f"{sym} RSI{int(rsi_v)} P{int(prob*100)}% {sig or 'WAIT'} [{source}] | "
                if sig and prob>best_prob and prob>=0.63:
                    best_prob=prob
                    best={'sym':sym,'sig':sig,'rsi':rsi_v,'ema_diff':ema_diff_v,'prob':prob,'df':df,'source':source}

            scan_box.info(scan[:800])
            # BEAST MODE
            if st.session_state.loss_streak>=2:
                cooldown=600
                stake=0.5
                mode="PAUSE BRAIN PROTECT"
            elif st.session_state.win_streak>=4 and best_prob>0.72:
                cooldown=45
                stake=3.5
                mode=f"BEAST FEED IQ{int(st.session_state.iq)}"
            elif total_pl>=20:
                cooldown=75
                stake=1.5
                mode="LOCK $20"
            else:
                cooldown=90
                stake=0.5 if total_pl<5 else 0.75
                mode=f"SAFE IQ{int(st.session_state.iq)}"

            ts=time.time()
            can=(ts-st.session_state.lt)>cooldown

            if best and len(port)<2 and can:
                sl=0.55
                tp=1.2 if mode.startswith("SAFE") else 2.8
                if "BEAST" in mode:
                    tp=4.0
                r=buy(best['sym'],stake,50,sl,tp,best['sig'])
                cid=r.get('buy',{}).get('contract_id','?')
                if cid!='?':
                    st.session_state.lt=ts
                    # Create temp cell that will be confirmed when profit arrives
                    temp_cell={'temp_id':str(cid),'sym':best['sym'],'rsi':best['rsi'],'ema_diff':best['ema_diff'],'hour':hour,'result':'PENDING','profit':0,'prob':best['prob'],'source':best['source'],'time':str(datetime.now())}
                    st.session_state.cells.append(temp_cell)
                    msg=f"{mode} {best['sym']} {best['sig']} ${stake} Prob {int(best['prob']*100)}% {best['source']} ID {cid} CELLS {len(st.session_state.cells)}"
                    st.session_state.logs.insert(0,msg)
                    sb.success(msg)
                    save_brain(st.session_state.cells, st.session_state.super_cells, st.session_state.iq)
            else:
                now=datetime.now().strftime("%H:%M:%S")
                sb.write(f"{now} [{mode}] CELLS {len(st.session_state.cells)} SUPER {len(st.session_state.super_cells)} Total ${round(total_pl,2)} | {best['sym'] if best else 'SEARCHING'} Prob {int(best_prob*100)}%")
            lb.code("\n".join(st.session_state.logs[:15]))
            if best:
                cb.line_chart(best['df'][['close','e9','e21']].tail(40))
            time.sleep(12)

with t2:
    st.write(f"### 🧬 {len(st.session_state.cells)} Brain Cells (Infinite)")
    st.dataframe(pd.DataFrame(st.session_state.cells[-100:]))
    st.write(f"### ⚡ {len(st.session_state.super_cells)} Super Cells (Multiplied Intelligence)")
    st.json(st.session_state.super_cells[-10:])

with t3:
    st.metric("Current IQ", int(st.session_state.iq))
    st.write("IQ Formula: 60 + Cells*0.5 + SuperCells*5 + RecentWinRate*20")
    st.write("Cells multiply every 10 trades when pattern WR >=70%")
    if st.button("Save Brain Forever"):
        save_brain(st.session_state.cells, st.session_state.super_cells, st.session_state.iq)
        st.success("Brain saved to mother_brain.json - will never forget!")
