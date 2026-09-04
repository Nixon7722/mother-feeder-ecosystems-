from flask import Flask, jsonify
import os, traceback, json, requests

app = Flask(__name__)

def get_headers():
    pat = os.environ.get("DERIV_TOKEN") or os.environ.get("PAT") or ""
    pat = pat.strip()
    app_id = os.environ.get("APP_ID", "1089").strip()
    return pat, app_id, {"Authorization": f"Bearer {pat}", "Deriv-App-ID": app_id}

@app.route("/")
def home():
    pat, app_id, _ = get_headers()
    return f"OK Live - PAT set: {len(pat)>10} len={len(pat)} APP_ID={app_id} - go to /accounts"

@app.route("/accounts")
def accounts():
    try:
        pat, app_id, headers = get_headers()
        if len(pat) < 10:
            return jsonify({"error": "DERIV_TOKEN missing or too short in Render Env", "len": len(pat)})
        r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers, timeout=15)
        return jsonify({"status": r.status_code, "data": r.json()})
    except Exception as e:
        return jsonify({"crash_in_accounts": str(e), "trace": traceback.format_exc()})

@app.route("/buy")
def buy():
    try:
        import websocket
        pat, app_id, headers = get_headers()
        if len(pat) < 10:
            return jsonify({"error": "DERIV_TOKEN missing"})
        # get accounts
        r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers, timeout=15)
        j = r.json()
        if r.status_code != 200:
            return jsonify({"error": "Deriv accounts failed", "status": r.status_code, "response": j})

        demo_id = "DOT84422096"
        # otp
        o = requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{demo_id}/otp", headers=headers, timeout=15)
        oj = o.json()
        ws_url = oj.get("data", {}).get("url")
        if not ws_url:
            return jsonify({"error": "no ws_url from OTP", "otp_response": oj})

        ws = websocket.create_connection(ws_url, timeout=10)
        ws.send(json.dumps({"proposal":1,"amount":1,"basis":"stake","contract_type":"CALL","currency":"USD","duration":1,"duration_unit":"m","underlying_symbol":"R_100"}))
        prop = json.loads(ws.recv())
        ws.close()
        return jsonify({"success": True, "account": demo_id, "proposal": prop})
    except Exception as e:
        return jsonify({"crash_in_buy": str(e), "trace": traceback.format_exc()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
