import os, requests
from flask import Flask, jsonify

app = Flask(__name__)

def get_headers():
    token = os.environ.get("DERIV_TOKEN","").strip()
    app_id = os.environ.get("APP_ID","").strip()
    headers = {
        "Authorization": f"Bearer {token}"
    }
    # Deriv uses app_id as query/header - keep both for safety
    if app_id:
        headers["Deriv-App-ID"] = app_id
        headers["App-ID"] = app_id
    return headers, token, app_id

@app.route("/")
def home():
    _, token, app_id = get_headers()
    return f"V14 FIXED - App {app_id} | Token len {len(token)} | Ready on backup-good-version"

@app.route("/accounts")
def accounts():
    headers, token, app_id = get_headers()
    if not token or not app_id:
        return jsonify({
            "error": "Missing DERIV_TOKEN or APP_ID in Render",
            "token_len": len(token),
            "app_id": app_id
        }), 400
    
    url = f"https://api.derivws.com/trading/v1/options/accounts?app_id={app_id}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        try:
            data = r.json()
        except:
            data = r.text[:2000]
        return jsonify({
            "v": "14-fixed",
            "branch": "backup-good-version",
            "status_code": r.status_code,
            "app_id_used": app_id,
            "deriv_reply": data
        })
    except Exception as e:
        return jsonify({"v": "14-fixed", "error": str(e)}), 500

@app.route("/ping")
def ping():
    return jsonify({"ok": True, "v": "14-fixed", "branch": "backup-good-version"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
