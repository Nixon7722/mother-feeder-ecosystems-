import streamlit as st, requests, json, websocket, time, pandas as pd
from datetime import datetime
st.set_page_config(page_title='MOTHER V14.4',layout='wide')
st.title('MOTHER V14.4 - FIXED')
TOKEN=st.secrets.get('DERIV_TOKEN','')
APP_ID=st.secrets.get('DERIV_APP_ID','34iR6HMxOfgO6m5LWOrAp')
AID='DOT94422096'
def otp_url():
 h={'Authorization':f'Bearer {TOKEN}','Deriv-App-ID':APP_ID}
 u=f'https://api.derivws.com/trading/v1/options/accounts/{AID}/otp'
 r=requests.post(u,headers=h,timeout=20)
 return r.json()['data']['url']
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
  m={'ticks_history':sym,'style':'candles','granularity':60,'count':100,'end':'latest'}
  w.send(json.dumps(m))
  r=json.loads(w.recv())
  w.close()
  return pd.DataFrame(r.get('candles',[]))
 except:
  return pd.DataFrame()
def buy(sym,typ):
 pr={'proposal':1,'amount':0.5,'basis':'stake','contract_type':typ,'currency':'USD','multiplier':50,'underlying_symbol':sym,'limit_order':{'stop_loss':0.55,'take_profit':1.5}}
 a=ws(pr)
 if 'proposal' in a:
  b=ws({'buy':a['proposal']['id'],'price':0.5})
  return b
 return a
def rsi_calc(df):
 d=df['close'].diff()
 g=d.where(d>0,0).ewm(alpha=1/14).mean()
 l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
 rs=g/l
 return 100-(100/(1+rs))
if 'logs' not in st.session_state:
 st.session_state.logs=[]
 st.session_state.lt=0
st.sidebar.header('V14.4 FIXED')
HUNT=['1HZ100V','R_100','R_50','BOOM1000']
sel=st.sidebar.multiselect('Hunt',HUNT,default=HUNT[:3])
auto=st.sidebar.checkbox('ENABLE BRAIN',value=False)
b1=st.empty()
b2=st.empty()
b3=st.empty()
if auto:
 for _ in range(10000):
  prof=ws({'profit_table':1,'description':1,'limit':20,'sort':'DESC'}).get('profit_table',{}).get('transactions',[])
  total=sum(float(x.get('sell_price',0)or 0)-float(x.get('buy_price',0)or 0) for x in prof)
  best=None
  scan=''
  for sym in sel:
   df=candles(sym)
   if df.empty or len(df)<30:
    continue
   df['e9']=df['close'].ewm(span=9).mean()
   df['e21']=df['close'].ewm(span=21).mean()
   df['rsi']=rsi_calc(df)
   last=df.iloc[-1]
   rv=float(last['rsi'])
   sig=None
   if float(last['e9'])>float(last['e21']) and 52<rv<75:
    sig='MULTUP'
   elif float(last['e9'])<float(last['e21']) and 25<rv<48:
    sig='MULTDOWN'
   scan+=f'{sym} RSI{int(rv)} {sig or "WAIT"} | '
   if sig:
    best={'sym':sym,'sig':sig}
  b2.info(scan)
  ts=time.time()
  can=(ts-st.session_state.lt)>85
  port=ws({'portfolio':1}).get('portfolio',{}).get('contracts',[])
  if best and len(port)<2 and can:
   r=buy(best['sym'],best['sig'])
   cid=r.get('buy',{}).get('contract_id','?')
   if cid!='?':
    st.session_state.lt=ts
    msg=f"BUY {best['sym']} {best['sig']} ID {cid} Total ${round(total,2)}"
    st.session_state.logs.insert(0,msg)
    b1.success(msg)
  else:
   now=datetime.now().strftime('%H:%M:%S')
   bn=best['sym'] if best else 'SEARCHING'
   b1.write(f'{now} {bn} Total ${round(total,2)}')
  b3.code('\n'.join(st.session_state.logs[:10]))
  time.sleep(12)
