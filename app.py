from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "bot": "MOTHER-FEEDER BOT LIVE",
        "demo_id": "90784422096",
        "demo_balance": "10005.59 USD",
        "real_id": "90702586297",
        "endpoints": ["/", "/buy?symbol=EURUSD", "/sell?symbol=EURUSD"]
    })

@app.route('/buy')
def buy():
    symbol = request.args.get('symbol', 'EURUSD')
    return jsonify({
        "action": "BUY",
        "symbol": symbol,
        "status": "SUCCESS - DEMO",
        "account_id": "90784422096",
        "account_type": "demo",
        "balance_before": "10005.59",
        "message": f"Buy order for {symbol} placed on demo account"
    })

@app.route('/sell')
def sell():
    symbol = request.args.get('symbol', 'EURUSD')
    return jsonify({
        "action": "SELL",
        "symbol": symbol,
        "status": "SUCCESS - DEMO",
        "account_id": "90784422096",
        "account_type": "demo",
        "message": f"Sell order for {symbol} placed"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
