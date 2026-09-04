from flask import Flask, jsonify
import os, requests
app = Flask(__name__)
def get_h():
 pat = (os.environ.get("DERIV_TOKEN") or "").strip()
 return {"Authorization": f"Bearer {pat}"}, pat
@app.route("/")
def home():
 return "V17 LIVE"
@app.route("/accounts")
def accounts():
 h, pat = get_h()
 r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=h, timeout=15)
 return jsonify({"status": r.status_code, "text": r.text[:1000], "len": len(pat)})
