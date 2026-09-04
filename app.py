from flask import Flask, jsonify, request
import os, sys, traceback

app = Flask(__name__)

@app.route("/")
def home():
    return "V15 Live - Debug Mode - go to /debug"

@app.route("/debug")
def debug():
    try:
        import requests, websocket
        pat = os.environ.get("DERIV_TOKEN") or os.environ.get("PAT") or os.environ.get("TOKEN") or "MISSING"
        app_id = os.environ.get("APP_ID", "NOT SET")
        info = {
            "pat_exists": pat != "MISSING",
            "pat_length": len(pat) if pat!="MISSING" else 0,
            "pat_starts_with": pat[:4] if pat!="MISSING" else "NONE",
            "app_id": app_id,
            "python_version": sys.version,
            "can_import_requests": True,
            "can_import_websocket": True
        }
        # try Deriv API
        headers = {"Authorization": f"Bearer {pat}", "Deriv-App-ID": app_id}
        r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers, timeout=10)
        info["deriv_status"] = r.status_code
        info["deriv_response"] = r.json()
        return jsonify(info)
    except Exception as e:
        return jsonify({"CRASH": str(e), "trace": traceback.format_exc()})

@app.route("/accounts")
def accounts():
    try:
        import requests
        pat = os.environ.get("DERIV_TOKEN") or os.environ.get("PAT") or os.environ.get("TOKEN")
        if not pat:
            return jsonify({"error": "DERIV_TOKEN missing in Render Environment"})
        app_id = os.environ.get("APP_ID", "34izQ97Q8ePS7YhgSZLJe")
        headers = {"Authorization": f"Bearer {pat}", "Deriv-App-ID": app_id}
        r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers, timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()})

@app.route("/buy")
def buy():
    try:
        import requests, websocket, json
        pat = os.environ.get("DERIV_TOKEN") or os.environ.get("PAT") or os.environ.get("TOKEN")
        if not pat:
            return jsonify({"error": "DERIV_TOKEN missing"})
        app_id = os.environ.get("APP_ID", "34izQ97Q8ePS7YhgSZLJe")
        headers = {"Authorization": f"Bearer {pat}", "Deriv-App-ID": app_id}
        
        accts = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers, timeout=10).json()
        data = accts.get("data", [])
        demo_id = "DOT84422096"
        if not data:
            return jsonify({"error": "no accounts returned", "raw": accts})
        
        otp = requests.post(f"https://api.derivws.com/trading/v1/options/accounts/{demo_id}/otp", headers=headers, timeout=10).json()
        ws_url = otp.get("data", {}).get("url")
        if not ws_url:
            return jsonify({"error": "no ws_url", "otp": otp})

        ws = websocket.create_connection(ws_url, timeout=10)
        ws.send(json.dumps({"proposal": 1, "amount": 1, "basis": "stake", "contract_type": "CALL", "currency": "USD", "duration": 1, "duration_unit": "m", "underlying_symbol": "R_100"}))
        prop = json.loads(ws.recv())
        ws.close()
        return jsonify({"account_used": demo_id, "proposal": prop, "ws_url_ok": True})
    except Exception as e:
        return jsonify({"BUY_CRASH": str(e), "trace": traceback.format_exc()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
