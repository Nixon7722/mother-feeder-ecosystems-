from flask import Flask, jsonify, request
import requests, os

app = Flask(__name__)

PAT = os.environ.get("DERIV_TOKEN") or os.environ.get("PAT") or os.environ.get("TOKEN")
APP_ID = os.environ.get("APP_ID", "34izQ97Q8ePS7YhgSZLJe")

@app.route("/")
def home():
    return "V15 Live - go to /buy?symbol=R_100&amount=1"

@app.route("/accounts")
def accounts():
    headers = {"Authorization": f"Bearer {PAT}", "Deriv-App-ID": APP_ID}
    r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers).json()
    return jsonify(r)

@app.route("/buy")
def buy():
    symbol = request.args.get("symbol", "R_100")
    amount = float(request.args.get("amount", "1"))

    headers = {"Authorization": f"Bearer {PAT}", "Deriv-App-ID": APP_ID}
    # get demo account - FIXED LOGIC
    accts = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers).json()
    demo_id = None
    for a in accts.get("data", []):
        if "demo" in str(a.get("account_type","")).lower() or "DOT" in a.get("account_id",""):
            if float(a.get("balance",0)) > 0 or a.get("account_id")=="DOT84422096":
                demo_id = a["account_id"]
                break
    if not demo_id:
        demo_id = accts["data"][0]["account_id"] # fallback to first

    # get OTP url for that demo
    otp = requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{demo_id}/otp", headers=headers).json()
    ws_url = otp["data"]["url"]

    import websocket, json
    ws = websocket.create_connection(ws_url)
    ws.send(json.dumps({
        "proposal": 1, "amount": amount, "basis": "stake",
        "contract_type": "CALL", "currency": "USD",
        "duration": 1, "duration_unit": "m",
        "underlying_symbol": symbol
    }))
    prop = json.loads(ws.recv())
    if "error" in prop:
        return jsonify(prop)
    pid = prop["proposal"]["id"]
    ws.send(json.dumps({"buy": pid, "price": amount}))
    result = json.loads(ws.recv())
    ws.close()
    return jsonify({"account_used": demo_id, "proposal": prop, "buy": result})

if __name__ == "__main__":
    app.run()
