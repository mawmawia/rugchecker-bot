from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# ====== CONFIG ======
BIRDEYE_API_KEY = "2e85b256bdb34a42a3b61039d5dec510"
# ====================

@app.route('/')
def home():
    return jsonify({
        "message": "RugChecker API v3.9.4",
        "status": "online",
        "endpoints": {
            "/check": "GET ?address=0x...&chain=base for token analysis",
            "/status": "GET for health check"
        }
    })

@app.route('/status')
def status():
    return jsonify({"status": "ok", "service": "RugChecker v3.9.4"})

@app.route('/check')
def check_token():
    address = request.args.get('address')
    chain = request.args.get('chain', 'base')
    
    if not address:
        return jsonify({"error": "Missing 'address' parameter"}), 400

    url = f"https://public-api.birdeye.so/defi/token_overview?address={address}&chain={chain}"
    headers = {"X-API-KEY": BIRDEYE_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get("success") and data.get("data"):
            token_data = data["data"]
            return jsonify({
                "contract_address": address,
                "chain": chain,
                "token_name": token_data.get("name"),
                "token_symbol": token_data.get("symbol"),
                "price_usd": token_data.get("price"),
                "liquidity": token_data.get("liquidity"),
                "market_cap": token_data.get("mc"),
                "holder_count": token_data.get("holder"),
                "verified": True
            })
        else:
            return jsonify({
                "contract_address": address, 
                "chain": chain, 
                "error": "Token not found on Birdeye"
            }), 404
            
    except Exception as e:
        return jsonify({"error": "Internal error", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
