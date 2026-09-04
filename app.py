from flask import Flask, jsonify
import os, requests
app = Flask(__name__)

@app.route("/")
def home(): return "V19 FINAL - With App-ID"

@app.route("/accounts")
def accounts():
    pat = os.environ.get("DERIV_TOKEN","").strip()
    app_id = os.environ.get("APP_ID","").strip()
    headers = {"Authorization": f"Bearer {pat}", "Deriv-App-ID": app_id}
    r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers, timeout=15)
    return jsonify({"status": r.status_code, "app_id_used": app_id, "len": len(pat), "text": r.text[:2000]})
