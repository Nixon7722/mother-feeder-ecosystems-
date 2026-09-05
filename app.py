import os, json, requests
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

CONFIG_FILE = "flex_config.json"
ADMIN_PASSWORD = "Nixon5998"

# --- LOAD / SAVE - Remember after reboot ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {
        "DERIV_TOKEN": os.environ.get("DERIV_TOKEN", "").strip(),
        "APP_ID": os.environ.get("APP_ID", "1089"),
        "ACCOUNT_ID": "DOT94422096"
    }

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def get_headers():
    cfg = load_config()
    token = cfg.get("DERIV_TOKEN", "").strip()
    app_id = cfg.get("APP_ID", "1089").strip()
    headers = {"Authorization": f"Bearer {token}"}
    if app_id:
        headers["Deriv-App-Id"] = app_id
        headers["App-Id"] = app_id
    return headers, token, app_id, cfg

# --- ADMIN PAGE INSIDE APP ---
ADMIN_HTML = """
<h2>🎛️ MOTHER FLEX - Inside-App Control</h2>
<p>Admin: Nixon5998 | This saves after reboot to flex_config.json</p>
<form method="POST">
    Admin Password: <input type="password" name="pwd" required><br><br>
    PAT Token (pat_...): <input type="text" name="token" value="{{cfg.DERIV_TOKEN}}" style="width:400px"><br><br>
    App ID: <input type="text" name="app_id" value="{{cfg.APP_ID}}"><br><br>
    Account ID (DOT... / ROT... / CR...): <input type="text" name="acc_id" value="{{cfg.ACCOUNT_ID}}"><br><br>
    <button type="submit">💾 SAVE - Remember After Reboot</button>
</form>
<br>
<a href="/accounts">Test Connection</a> | <a href="/">Home</a>
{% if msg %}<p><b>{{msg}}</b></p>{% endif %}
"""

@app.route('/')
def home():
    _, token, app_id, cfg = get_headers()
    return f"V13 LIVE - App {app_id} | Account {cfg.get('ACCOUNT_ID')} | Token len {len(token)} | <a href='/admin'>Admin Panel</a>"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    cfg = load_config()
    msg = ""
    if request.method == "POST":
        if request.form.get("pwd") != ADMIN_PASSWORD:
            msg = "❌ Wrong password"
        else:
            cfg["DERIV_TOKEN"] = request.form.get("token", "").strip()
            cfg["APP_ID"] = request.form.get("app_id", "").strip()
            cfg["ACCOUNT_ID"] = request.form.get("acc_id", "").strip()
            save_config(cfg)
            msg = f"✅ SAVED! Will remember after reboot. Account={cfg['ACCOUNT_ID']}"
    return render_template_string(ADMIN_HTML, cfg=cfg, msg=msg)

@app.route('/accounts')
def accounts():
    headers, token, app_id, cfg = get_headers()
    acc_id = cfg.get("ACCOUNT_ID", "")
    if not token or not app_id:
        return jsonify({"error": "Missing keys - Go to /admin", "app_id": app_id}), 400
    
    # Auto-fetch all your accounts - No typing
    url_all = f"https://api.deriv.com/trading/v1/accounts?app_id={app_id}"
    url_one = f"https://api.deriv.com/trading/v1/options/accounts/{acc_id}?app_id={app_id}"
    
    try:
        # Try to get list first
        r_list = requests.get(url_all, headers=headers, timeout=15)
        try: data_list = r_list.json()
        except: data_list = r_list.text[:1000]
        
        r_one = requests.get(url_one, headers=headers, timeout=15)
        try: data_one = r_one.json()
        except: data_one = r_one.text[:1000]
        
        return jsonify({
            "working_branch": "V13-working-base",
            "active_account": acc_id,
            "all_accounts_response": {"status": r_list.status_code, "data": data_list},
            "active_account_response": {"status": r_one.status_code, "data": data_one},
            "hint": "If active_account fails, your ACCOUNT_ID in /admin is wrong. Use loginid from all_accounts_response"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ping')
def ping():
    return jsonify({"ok": True, "v": "13-working-flex"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
