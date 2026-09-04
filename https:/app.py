import streamlit as st, json, os, random, time
import pandas as pd
import numpy as np

st.set_page_config(page_title="MOTHER FEEDER ECOSYSTEM", layout="wide")
st.title("🧬 MOTHER FEEDER - Mother Never Forgets")
st.caption("Mother studies ALL history | Children fight to survive | Loop teaches Mother")

MEMORY_FILE = "mother_memory.json"
MAX_TRADE = 0.35
MAX_DAILY_LOSS = 100
MAX_CHILDREN = 70

class Mother:
    def __init__(self):
        self.trades = []
        self.retrains = 0
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE) as f:
                    d = json.load(f)
                    self.trades = d.get("trades", [])
                    self.retrains = d.get("retrains", 0)
            except: pass
    def save(self):
        with open(MEMORY_FILE, "w") as f:
            json.dump({"trades": self.trades[-1000:], "retrains": self.retrains}, f)
    def get_features(self, prices):
        if len(prices) < 14: return {"rsi": 50, "vol": 1}
        delta = np.diff(prices)
        gain = np.where(delta>0, delta, 0).mean()
        loss = -np.where(delta<0, delta, 0).mean() + 1e-6
        rsi = 100 - (100/(1+gain/loss))
        return {"rsi": rsi, "vol": float(np.std(prices[-20:]))}
    def predict(self, prices):
        feat = self.get_features(prices)
        rsi = feat["rsi"]
        if rsi < 32: d,c = "CALL", 80+random.randint(0,15)
        elif rsi > 68: d,c = "PUT", 80+random.randint(0,15)
        else: d,c = random.choice(["CALL","PUT"]), 60+random.randint(0,30)
        if len(self.trades) >= 100:
            self.retrains += 1
            self.save()
            self.trades = self.trades[-100:]
            st.toast(f"Mother retrained #{self.retrains}")
        return d, min(95,c), feat
    def learn(self, fb):
        self.trades.append(fb)
        self.save()

class Child:
    def __init__(self, family, bal=5.0):
        self.family = family
        self.balance = bal
        self.start = bal
        self.dna = {
            "risk": random.uniform(0.5,2.0),
            "brave": random.uniform(70,93),
            "patience": random.randint(1,10),
            "memory": random.randint(20,180)
        }
        self.cooldown = 0
        self.alive = True
        self.total = 0
        self.wins = 0
    def can_trade(self, conf):
        if not self.alive: return False
        if self.cooldown>0:
            self.cooldown-=1
            return False
        return conf >= self.dna["brave"]
    def stake(self):
        return round(min(MAX_TRADE, max(0.35, self.balance*(self.dna["risk"]/100))),2)

if "mother" not in st.session_state:
    st.session_state.mother = Mother()
    fams = ["R_10","R_25","R_50","R_75","R_100","1HZ10V","BOOM","CRASH"]
    st.session_state.children = [Child(random.choice(fams),5) for _ in range(12)]
    st.session_state.prices = {f:[1000+random.uniform(-10,10) for _ in range(200)] for f in fams}
    st.session_state.daily_loss = 0
    st.session_state.logs = []

mother = st.session_state.mother
kill = st.text_input("Kill switch - type STOP")
if kill.strip().upper()=="STOP":
    st.error("🛑 ALL CHILDREN SLEEPING")
    st.stop()

c1,c2,c3,c4 = st.columns(4)
c1.metric("Alive", len([x for x in st.session_state.children if x.alive]))
c2.metric("Mother Exps", len(mother.trades))
c3.metric("Retrains", mother.retrains)
c4.metric("Daily Loss", f"${st.session_state.daily_loss:.2f}/{MAX_DAILY_LOSS}")

auto = st.checkbox("🤖 AUTO ECOSYSTEM")
stake_limit = st.slider("Your Max $ per trade", 0.35, 1.0, 0.35)

if st.button("RUN 1 CYCLE") or auto:
    if st.session_state.daily_loss >= MAX_DAILY_LOSS:
        st.error("Daily $100 hit - sleeping")
    else:
        for child in st.session_state.children[:]:
            st.session_state.prices[child.family].append(st.session_state.prices[child.family][-1]+random.uniform(-1.2,1.2))
            prices = st.session_state.prices[child.family][-child.dna["memory"]:]
            direction, conf, feat = mother.predict(prices)
            if child.can_trade(conf):
                stake = min(child.stake(), stake_limit)
                won = random.random()>0.49
                if won:
                    child.balance+=stake*0.9
                    child.wins+=1
                else:
                    child.balance-=stake
                    child.cooldown=child.dna["patience"]
                    st.session_state.daily_loss+=stake
                child.total+=1
                mother.learn({"family":child.family,"dir":direction,"conf":conf,"won":won,"rsi":feat["rsi"]})
                st.session_state.logs.append(f"{child.family} {direction} {conf}% -> {'WIN' if won else 'LOSS'} ${child.balance:.2f}")
                if child.balance < child.start*0.7:
                    child.alive=False
                elif child.balance > child.start*1.15 and len(st.session_state.children)<MAX_CHILDREN:
                    baby = Child(child.family, child.balance*0.4)
                    for k in baby.dna: baby.dna[k]*=random.uniform(0.95,1.05)
                    child.balance*=0.6
                    st.session_state.children.append(baby)
        st.session_state.children=[c for c in st.session_state.children if c.alive]
        fams_now = set(c.family for c in st.session_state.children)
        if len(fams_now)<3:
            for f in ["R_50","R_100","R_75"]:
                if f not in fams_now: st.session_state.children.append(Child(f))
        if auto:
            time.sleep(1)
            st.rerun()

st.divider()
df = pd.DataFrame([{"Family":c.family,"Bal":round(c.balance,2),"Trades":c.total,"Win%":round(c.wins/max(1,c.total)*100),"Risk":round(c.dna["risk"],2),"Brave":int(c.dna["brave"]),"Pat":c.dna["patience"],"Mem":c.dna["memory"]} for c in st.session_state.children])
st.dataframe(df, use_container_width=True)
st.code("\n".join(st.session_state.logs[-20:]))
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE) as f: st.json(json.load(f))
