from flask import Flask, request, jsonify
import os
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"bot":"LIVE","demo_id":"90784422096","balance":"10005.59","endpoints":["/buy?symbol=EURUSD"]})

@app.route('/buy')
def buy():
    s = request.args.get('symbol','EURUSD')
    return jsonify({"action":"BUY","symbol":s,"status":"SUCCESS DEMO","account":"90784422096"})

@app.route('/sell')
def sell():
    s = request.args.get('symbol','EURUSD')
    return jsonify({"action":"SELL","symbol":s,"status":"SUCCESS DEMO"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
