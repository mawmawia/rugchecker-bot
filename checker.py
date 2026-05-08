from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "RugChecker API v4.0",
        "status": "online",
        "note": "Now using DexScreener - no API key needed"
    })

@app.route('/check')
def check_token():
    address = request.args.get('address')
    chain = request.args.get('chain', 'solana')

    if not address:
        return jsonify({"error": "Missing 'address' parameter"}), 400

    # Use DexScreener - free, no key, works for WSOL
    url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("pairs") and len(data["pairs"]) > 0:
            pair = data["pairs"][0] # Take first trading pair
            return jsonify({
                "contract_address": address,
                "chain": chain,
                "token_name": pair.get("baseToken", {}).get("name"),
                "token_symbol": pair.get("baseToken", {}).get("symbol"),
                "price_usd": pair.get("priceUsd"),
                "liquidity_usd": pair.get("liquidity", {}).get("usd"),
                "fdv": pair.get("fdv"),
                "dex": pair.get("dexId"),
                "verified": True
            })
        else:
            return jsonify({
                "contract_address": address,
                "chain": chain,
                "error": "No trading pairs found"
            }), 404

    except Exception as e:
        return jsonify({"error": "Internal error", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
