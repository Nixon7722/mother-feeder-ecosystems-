 import os, json, asyncio, threading, time, random, math
from datetime import datetime
from flask import Flask, request, redirect, jsonify
import websockets
from collections import deque

app = Flask(__name__)

# === CONFIG ===
DATA_FILE = "data.json"
BRAIN_DIR = "deriv_brain"
BRAIN_FILE = f"{BRAIN_DIR}/mother_memory.json"

DEFAULTS = {
    "deriv_token": "",
    "app_id": "1089",
    "admin_pass": "Nixon5998",
    "max_stake": 0.35,
    "max_daily_loss": 100,
    "max_population": 70
}

MARKETS = [
    "R_10", "R_25", "R_50", "R_75", "R_100",
    "R_10_1s", "R_25_1s", "R_50_1s", "R_75_1s", "R_100_1s",
    "BOOM1000", "BOOM500", "BOOM300", "CRASH1000", "CRASH500", "CRASH300",
    "JD10", "JD25", "JD50", "JD75", "JD100",
    "frxEURUSD", "frxGBPUSD", "frxUSDJPY"
]

os.makedirs(BRAIN_DIR, exist_ok=True)

def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return {**default, **json.load(f)}
        except: pass
    return default.copy()

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

config = load_json(DATA_FILE, DEFAULTS)

# === MOTHER BRAIN ===
class MotherBrain:
    def __init__(self):
        self.memory = load_json(BRAIN_FILE, {
            "trades_seen": 0,
            "ticks_seen": {},
            "patterns": {}, # feature_hash -> {wins, losses}
            "model_version": 1
        })
        self.ticks = {m: deque(maxlen=500) for m in MARKETS}
        self.confidence = 0
        self.last_signal = "WAIT"

    def save(self):
        save_json(BRAIN_FILE, self.memory)

    def add_tick(self, symbol, price, epoch):
        if symbol not in self.ticks:
            self.ticks[symbol] = deque(maxlen=500)
        self.ticks[symbol].append({"price": price, "epoch": epoch})
        self.memory["ticks_seen"][symbol] = self.memory["ticks_seen"].get(symbol, 0) + 1
        if self.memory["ticks_seen"][symbol] % 500 == 0:
            self.save()

    def extract_features(self, symbol):
        ticks = list(self.ticks.get(symbol, []))
        if len(ticks) < 50:
            return None
        prices = [t["price"] for t in ticks]
        # Simple features
        rsi = self.calc_rsi(prices, 14)
        sma20 = sum(prices[-20:])/20
        sma50 = sum(prices[-50:])/50 if len(prices)>=50 else sma20
        vol = math.sqrt(sum((p - sma20)**2 for p in prices[-20:])/20)
        last100_winrate = 0.5 # placeholder from patterns
        hour = datetime.utcnow().hour

        return {
            "rsi": rsi,
            "sma20": sma20,
            "sma50": sma50,
            "vol": vol,
            "hour": hour,
            "price": prices[-1],
            "trend": 1 if sma20 > sma50 else -1
        }

    def calc_rsi(self, prices, period=14):
        if len(prices) < period+1: return 50
        gains, losses = 0, 0
        for i in range(-period, 0):
            diff = prices[i] - prices[i-1]
            if diff > 0: gains += diff
            else: losses -= diff
        if losses == 0: return 70
        rs = gains / losses
        return 100 - (100/(1+rs))

    def predict(self, symbol):
        feat = self.extract_features(symbol)
        if not feat:
            return "WAIT", 0, feat

        # Mother logic - learns from patterns
        # Base score from RSI + trend + hour pattern
        score = 50
        if feat["rsi"] < 30: score += 20 # oversold -> CALL
        if feat["rsi"] > 70: score -= 20 # overbought -> PUT
        if feat["trend"] == 1: score += 10
        if feat["trend"] == -1: score -= 10

        # Learn from past patterns
        key = f"{symbol}_{int(feat['rsi']/10)}_{feat['trend']}_{feat['hour']}"
        pat = self.memory["patterns"].get(key, {"wins":1, "losses":1})
        winrate = pat["wins"] / (pat["wins"]+pat["losses"])
        score = score * 0.7 + winrate*100 * 0.3

        confidence = abs(score-50)*2 # 0-100
        signal = "CALL" if score > 52 else "PUT" if score < 48 else "WAIT"

        self.last_signal = signal
        self.confidence = confidence
        return signal, confidence, feat

    def feedback(self, symbol, feat, signal, result_win):
        if not feat: return
        key = f"{symbol}_{int(feat['rsi']/10)}_{feat['trend']}_{feat['hour']}"
        if key not in self.memory["patterns"]:
            self.memory["patterns"][key] = {"wins":1, "losses":1}
        if result_win:
            self.memory["patterns"][key]["wins"] += 1
        else:
            self.memory["patterns"][key]["losses"] += 1
        self.memory["trades_seen"] += 1
        if self.memory["trades_seen"] % 100 == 0:
            self.memory["model_version"] += 1
            self.save() # Retrain every 100

mother = MotherBrain()

# === CHILDREN ECOSYSTEM ===
class Child:
    def __init__(self, family, parent_dna=None):
        self.id = f"{family}_{random.randint(1000,9999)}"
        self.family = family # R_50, R_100, R_75 etc for diversity
        self.balance = 10.0
        self.start_balance = 10.0
        self.alive = True
        self.trades = 0
        self.last_loss_time = 0
        if parent_dna:
            # mutate 5%
            self.dna = {
                k: max(0.1, v * random.uniform(0.95,1.05))
                for k,v in parent_dna.items()
            }
        else:
            self.dna = {
                "risk": random.uniform(0.5, 2.0), # stake %
                "brave": random.uniform(60, 80), # confidence required
                "patience": random.uniform(5, 30), # seconds after loss
                "memory": random.randint(20, 100) # ticks to look back
            }

    def to_dict(self):
        return {"id": self.id, "family": self.family, "balance": round(self.balance,2), "dna": self.dna, "alive": self.alive, "trades": self.trades}

ecosystem = {
    "children": [Child(random.choice(["R_50","R_100","R_75"])) for _ in range(10)],
    "daily_loss": 0,
    "stopped": False,
    "total_trades": 0
}

def get_alive_children():
    return [c for c in ecosystem["children"] if c.alive]

def check_diversity():
    families = set(c.family for c in get_alive_children())
    return len(families) >= 3 or len(get_alive_children()) < 3

# === DERIV LIVE FEED ===
deriv_state = {"connected": False, "balance": "No token", "loginid": "-", "last_tick": "-"}

async def deriv_loop():
    global deriv_state
    while True:
        try:
            if not config["deriv_token"]:
                deriv_state["balance"] = "Set token in /admin"
                await asyncio.sleep(5)
                continue
            if ecosystem["stopped"]:
                await asyncio.sleep(1)
                continue

            uri = f"wss://ws.derivws.com/websockets/v3?app_id={config['app_id']}"
            async with websockets.connect(uri) as ws:
                await ws.send(json.dumps({"authorize": config["deriv_token"]}))
                auth_resp = json.loads(await ws.recv())
                if "error" in auth_resp:
                    deriv_state["balance"] = f"Auth error: {auth_resp['error']['message']}"
                    await asyncio.sleep(5)
                    continue

                deriv_state["connected"] = True
                deriv_state["loginid"] = auth_resp["authorize"]["loginid"]

                # Subscribe to all markets
                for m in MARKETS:
                    await ws.send(json.dumps({"ticks": m, "subscribe": 1}))

                # Balance
                await ws.send(json.dumps({"balance": 1, "subscribe": 1}))

                async for msg in ws:
                    data_msg = json.loads(msg)

                    if "tick" in data_msg:
                        t = data_msg["tick"]
                        symbol = t["symbol"]
                        mother.add_tick(symbol, t["quote"], t["epoch"])
                        deriv_state["last_tick"] = f"{symbol} {t['quote']}"

                        # Mother predicts
                        signal, conf, feat = mother.predict(symbol)

                        # Children try to trade if confidence >70%
                        if conf > 70 and signal!= "WAIT" and not ecosystem["stopped"]:
                            if ecosystem["daily_loss"] >= config["max_daily_loss"]:
                                ecosystem["stopped"] = True # ALL sleep
                                continue

                            for child in get_alive_children():
                                if child.family!= symbol and random.random() > 0.3:
                                    continue # child sticks to its family mostly
                                if conf < child.dna["brave"]: continue
                                if time.time() - child.last_loss_time < child.dna["patience"]: continue

                                # Trade
                                stake = min(config["max_stake"], child.balance * (child.dna["risk"]/100))
                                if stake < 0.35: stake = 0.35
                                # Here you would call proposal + buy - simplified for V1 (logs)
                                child.trades += 1
                                ecosystem["total_trades"] += 1

                                # Simulate result feedback for brain (replace with real buy result)
                                # In real V1 we will plug proposal->buy and get result
                                win = random.random() > 0.45 # placeholder until real trade result
                                mother.feedback(symbol, feat, signal, win)

                                if win:
                                    child.balance += stake * 0.9
                                    if child.balance > child.start_balance * 1.15:
                                        # Reproduce
                                        if len(ecosystem["children"]) < config["max_population"] and check_diversity():
                                            baby = Child(child.family, child.dna)
                                            baby.balance = child.balance * 0.4
                                            child.balance *= 0.6
                                            ecosystem["children"].append(baby)
                                else:
                                    child.balance -= stake
                                    child.last_loss_time = time.time()
                                    ecosystem["daily_loss"] += stake
                                    if child.balance < child.start_balance * 0.7:
                                        child.alive = False

                    if "balance" in data_msg:
                        deriv_state["balance"] = f"{data_msg['balance']['balance']} {data_msg['balance']['currency']}"

        except Exception as e:
            deriv_state["connected"] = False
            deriv_state["balance"] = f"Reconnecting... {e}"
            await asyncio.sleep(3)

def start_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(deriv_loop())

threading.Thread(target=start_loop, daemon=True).start()

# === FLASK ROUTES ===
@app.route("/")
def home():
    alive = get_alive_children()
    return f"""
    <h2>MOTHER FEEDER V1 - LIVE</h2>
    <p><b>Deriv:</b> {deriv_state['loginid']} | {deriv_state['balance']} | Connected: {deriv_state['connected']}</p>
    <p><b>Mother:</b> Ticks: {sum(mother.memory['ticks_seen'].values())} | Trades Seen: {mother.memory['trades_seen']} | Model v{mother.memory['model_version']} | Last Signal: {mother.last_signal} {int(mother.confidence)}%</p>
    <p><b>Ecosystem:</b> Alive {len(alive)}/{len(ecosystem['children'])} | Daily Loss: {ecosystem['daily_loss']:.2f}/{config['max_daily_loss']} | Total Trades: {ecosystem['total_trades']} | Stopped: {ecosystem['stopped']}</p>
    <p><b>Last Tick:</b> {deriv_state['last_tick']}</p>
    <a href='/admin'>Admin - Change Token / Demo-Real</a> | <a href='/ecosystem'>View Children</a> | <a href='/brain'>Mother Memory</a> | <a href='/stop'>STOP ALL</a> | <a href='/start'>START</a>
    """

@app.route("/ecosystem")
def eco():
    return jsonify([c.to_dict() for c in ecosystem["children"]])

@app.route("/brain")
def brain():
    return jsonify(mother.memory)

@app.route("/stop")
def stop():
    ecosystem["stopped"] = True
    return "STOPPED - ALL SLEEP <a href='/'>Home</a>"

@app.route("/start")
def start():
    ecosystem["stopped"] = False
    ecosystem["daily_loss"] = 0
    return "STARTED <a href='/'>Home</a>"

@app.route("/admin", methods=["GET","POST"])
def admin():
    global config
    if request.method == "POST":
        if request.form.get("admin_pass")!= config["admin_pass"]:
            return "Wrong password <a href='/admin'>Back</a>"
        config["deriv_token"] = request.form.get("deriv_token","").strip()
        config["app_id"] = request.form.get("app_id","").strip() or config["app_id"]
        save_json(DATA_FILE, config)
        return redirect("/")
    return f"""
    <h2>Admin - Independent Control</h2>
    <form method="post">
    Password: <input name="admin_pass" type="password" value="{config['admin_pass']}"><br><br>
    Deriv Token (change when expires):<br>
    <input name="deriv_token" style="width:500px" value="{config['deriv_token']}" placeholder="Paste new token"><br><br>
    App ID:<br>
    <input name="app_id" style="width:500px" value="{config['app_id']}"><br><br>
    <button>SAVE - Remember After Reboot</button>
    </form>
    <p>Max Stake: ${config['max_stake']} | Max Daily Loss: ${config['max_daily_loss']} | Max Pop: {config['max_population']}</p>
    <a href="/">Home</a>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
