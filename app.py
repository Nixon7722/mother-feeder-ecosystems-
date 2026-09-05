import os, requests
from flask import Flask, jsonify

app = Flask(__name__)

def get_headers():
    token = os.environ.get("DERIV_TOKEN","").strip()
    app_id = os.environ.get("APP_ID","").strip()  # 34iR6HMxOfgO6m5LWOrAp
    return {
        "Authorization": f"Bearer {token}",
        "Deriv-App-ID": app_id
    }, token, app_id

@app.route("/")
def home():
    _, token, app_id = get_headers()
    return f"V14 RESTORED - App {app_id} | Token {len(token)} chars | <a href='/accounts'>/accounts</a>"

@app.route("/accounts")
def accounts():
    headers, token, app_id = get_headers()
    if not token or not app_id:
        return jsonify({"error": "Missing DERIV_TOKEN or APP_ID in Render env", "app_id": app_id, "token_len": len(token)})
    
    url = "https://api.derivws.com/trading/v1/options/accounts"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        # V14 logic: just return what Deriv says
        try:
            data = r.json()
        except:
            data = r.text[:2000]
        
        return jsonify({
            "v": "14-restored",
            "status_code": r.status_code,
            "app_id_used": app_id,
            "deriv_reply": data
        })
    except Exception as e:
        return jsonify({"v": "14-restored", "error": str(e)}), 500

@app.route("/ping")
def ping():
    return jsonify({"ok": True, "v": "14"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
