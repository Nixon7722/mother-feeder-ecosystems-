import os, requests
from flask import Flask, jsonify
app = Flask(__name__)

def get_headers():
    token = os.environ.get("DERIV_TOKEN","").strip()
    app_id = os.environ.get("APP_ID","").strip()
    headers = {"Authorization": f"Bearer {token}"}
    if app_id:
        headers["Deriv-App-ID"] = app_id
        headers["App-ID"] = app_id
    return headers, token, app_id

@app.route("/")
def home():
    _, token, app_id = get_headers()
    return f"V13 LIVE - App {app_id} | Token len {len(token)}"

@app.route("/accounts")
def accounts():
    headers, token, app_id = get_headers()
    if not token or not app_id:
        return jsonify({"error": "Missing keys", "app_id": app_id}), 400
    url = f"https://api.deriv.com/trading/v1/options/accounts?app_id={app_id}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        try: data = r.json()
        except: data = r.text[:1000]
        return jsonify({"v": "13-working", "branch": "V13-working-base", "status": r.status_code, "data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ping")
def ping():
    return jsonify({"ok": True, "v": "13-working"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
