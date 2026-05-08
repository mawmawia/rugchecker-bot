from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# ====== CONFIG ======
BIRDEYE_API_KEY = os.environ.get("2e85b256bdb34a42a3b61039d5dec510")  # We'll set this in Railway
# ====================

@app.route('/')
def home():
    return jsonify({
        "message": "RugChecker API v3.9.4",
        "status": "online"
    })

@app.route('/status')
def status():
    return jsonify({"status": "ok", "service": "RugChecker v3.9.4"})

@app.route('/check')
def check_token():
    address = request.args.get('address')
    
    if not address:
        return jsonify({"error": "address parameter required"}), 400
    
    try:
        # Birdeye API call for Base chain
        url = f"https://public-api.birdeye.so/defi/token_overview?address={address}"
        headers = {
            "X-API-KEY": BIRDEYE_API_KEY,
            "x-chain": "base"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('success') and data.get('data'):
            result = data['data']
            return jsonify({
                "token_name": result.get('name'),
                "token_symbol": result.get('symbol'),
                "total_supply": result.get('supply'),
                "decimals": result.get('decimals'),
                "verified": True,
                "contract_address": address,
                "price": result.get('price'),
                "market_cap": result.get('mc'),
                "flags": []
            })
        else:
            return jsonify({
                "error": "Token not found on Birdeye",
                "contract_address": address
            }), 404
            
    except Exception as e:
        return jsonify({
            "error": "Internal error", 
            "details": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
