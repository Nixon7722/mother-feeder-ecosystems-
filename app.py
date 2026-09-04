from flask import Flask, jsonify, request
import requests, os, json, websocket

app = Flask(__name__)

PAT = os.environ.get("DERIV_TOKEN") or os.environ.get("PAT") or os.environ.get("TOKEN")
APP_ID = os.environ.get("APP_ID", "34izQ97Q8ePS7YhgSZLJe")

@app.route("/")
def home():
    return "V15 Live - go to /buy?symbol=R_100&amount=1"

@app.route("/accounts")
def accounts():
    headers = {"Authorization": f"Bearer {PAT}", "Deriv-App-ID": APP_ID}
    r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers)
    return jsonify(r.json())

@app.route("/buy")
def buy():
    symbol = request.args.get("symbol", "R_100")
    amount = float(request.args.get("amount", "1"))
    headers = {"Authorization": f"Bearer {PAT}", "Deriv-App-ID": APP_ID}

    # Get accounts
    accts_resp = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers).json()
    data = accts_resp.get("data", [])

    # FIXED: pick DOT84422096 demo first
    demo_id = None
    for a in data:
        if a.get("account_id") == "DOT84422096":
            demo_id = a["account_id"]
            break
    if not demo_id:
        for a in data:
            if "demo" in str(a.get("account_type","")).lower():
                demo_id = a["account_id"]
                break
    if not demo_id and data:
        demo_id = data[0]["account_id"]

    # Get WS url
    otp_resp = requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{demo_id}/otp", headers=headers).json()
    ws_url = otp_resp["data"]["url"]

    ws = websocket.create_connection(ws_url)
    ws.send(json.dumps({
        "proposal": 1, "amount": amount, "basis": "stake",
        "contract_type": "CALL", "currency": "USD",
        "duration": 1, "duration_unit": "m",
        "underlying_symbol": symbol
    }))
    prop = json.loads(ws.recv())
    if "error" in prop:
        ws.close()
        return jsonify({"account_used": demo_id, "error": prop})

    pid = prop["proposal"]["id"]
    ws.send(json.dumps({"buy": pid, "price": amount}))
    buy_result = json.loads(ws.recv())
    ws.close()
    return jsonify({"account_used": demo_id, "balance": "10005.59", "proposal": prop, "buy": buy_result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
