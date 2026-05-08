from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# ====== CONFIG ======
BIRDEYE_API_KEY = "d9038446c7b24aaa90ef07b22c719cb7"
# ====================

@app.route('/')
def home():
    return jsonify({
        "message": "RugChecker API v3.9.5",
        "status": "online",
        "endpoints": {
            "/check": "GET ?address=...&chain=solana for token price check",
            "/status": "GET for health check"
        }
    })

@app.route('/status')
def status():
    return jsonify({"status": "ok", "service": "RugChecker v3.9.5"})

@app.route('/check')
def check_token():
    address = request.args.get('address')
    chain = request.args.get('chain', 'solana')
    
    if not address:
        return jsonify({"error": "Missing 'address' parameter"}), 400

    # Use /defi/price endpoint - works on free tier
    url = f"https://public-api.birdeye.so/defi/price?address={address}"
    headers = {"X-API-KEY": BIRDEYE_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get("success") and data.get("data"):
            return jsonify({
                "contract_address": address,
                "chain": chain,
                "price_usd": data["data"].get("value"),
                "verified": True,
                "note": "Price data from Birdeye free tier"
            })
        else:
            return jsonify({
                "contract_address": address, 
                "chain": chain, 
                "error": "Token not found",
                "birdeye_response": data
            }), 404
            
    except Exception as e:
        return jsonify({"error": "Internal error", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
