from flask import Flask, jsonify
import os, traceback, json, requests

app = Flask(__name__)

def headers():
    pat = (os.environ.get("DERIV_TOKEN") or os.environ.get("PAT") or "").strip()
    app_id = (os.environ.get("APP_ID") or "1089").strip()
    return {"Authorization": f"Bearer {pat}", "Deriv-App-ID": app_id}, pat

@app.route("/")
def home():
    h, pat = headers()
    return f"V16 LIVE - token len {len(pat)} - go to /accounts"

@app.route("/accounts")
def accounts():
    try:
        h, pat = headers()
        if len(pat) < 20: return jsonify({"error": "PAT missing in Render ENV", "len": len(pat)})
        r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=h, timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()})

@app.route("/buy")
def buy():
    try:
        import websocket
        h, pat = headers()
        r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=h, timeout=15).json()
        demo = "DOT84422096"
        # get otp
        o = requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{demo}/otp", headers=h, timeout=15).json()
        url = o.get("data", {}).get("url")
        if not url: return jsonify({"otp_failed": o})
        ws = websocket.create_connection(url, timeout=10)
        ws.send(json.dumps({"proposal":1,"amount":1,"basis":"stake","contract_type":"CALL","currency":"USD","duration":1,"duration_unit":"m","underlying_symbol":"R_100"}))
        ans = ws.recv()
        ws.close()
        return jsonify({"account": demo, "result": json.loads(ans)})
    except Exception as e:
        return jsonify({"buy_error": str(e), "trace": traceback.format_exc()})
