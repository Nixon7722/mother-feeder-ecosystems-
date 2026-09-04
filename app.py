from flask import Flask, jsonify
import os, requests

app = Flask(__name__)

def get_h():
    pat = (os.environ.get("DERIV_TOKEN") or os.environ.get("PAT") or "").strip()
    app_id = (os.environ.get("APP_ID") or "1089").strip()
    return {"Authorization": f"Bearer {pat}", "Deriv-App-ID": app_id}, pat

@app.route("/")
def home():
    h, pat = get_h()
    return f"V17 LIVE len={len(pat)} go to /accounts"

@app.route("/accounts")
def accounts():
    h, pat = get_h()
    if len(pat) < 20:
        return jsonify({"error": "PAT empty in Render", "len": len(pat)})
    r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=h, timeout=15)
    # DON'T crash on empty body
    try:
        data = r.json()
    except:
        data = {"raw_text": r.text[:500], "status": r.status_code}
    return jsonify({"http_status": r.status_code, "deriv_response": data, "pat_len": len(pat)})

@app.route("/buy")
def buy():
    return jsonify({"msg": "first fix /accounts, then we fix buy"})
