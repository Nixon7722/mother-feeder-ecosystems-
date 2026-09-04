import os, json, asyncio, requests, websockets
from flask import Flask, jsonify

app = Flask(__name__)

APP_ID = "34iR6HMxOfgO6m5LWOrAp"

def get_token():
    return os.getenv("DERIV_TOKEN")

@app.route("/")
def home():
    return "V15 Live - go to /buy"

@app.route("/buy")
def buy():
    PAT = get_token()
    if not PAT:
        return jsonify({"error": "Set DERIV_TOKEN in Render"}), 500
    headers = {"Authorization": f"Bearer {PAT}", "Deriv-App-ID": APP_ID}
    r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers, timeout=15)
    if r.status_code!= 200:
        return jsonify({"step":"accounts","status":r.status_code,"response":r.text}), 500
    data = r.json().get('data',[])
    demo = [a for a in data if a.get('group')=='demo']
    if not demo:
        return jsonify({"error":"no demo","all":data}), 500
    acc_id = demo[0]['account_id']
    r2 = requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{acc_id}/otp", headers=headers, timeout=15)
    if r2.status_code!= 200:
        return jsonify({"step":"otp","response":r2.text}), 500
    ws_url = r2.json()['data']['url']
    async def do_trade():
        async with websockets.connect(ws_url) as ws:
            await ws.send(json.dumps({"proposal":1,"amount":1,"basis":"stake","contract_type":"DIGITMATCH","currency":"USD","duration":2,"duration_unit":"t","underlying_symbol":"1HZ50V","barrier":"1"}))
            prop = json.loads(await ws.recv())
            if "error" in prop: return prop
            await ws.send(json.dumps({"buy": prop['proposal']['id'], "price": prop['proposal']['ask_price']}))
            return json.loads(await ws.recv())
    result = asyncio.run(do_trade())
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
