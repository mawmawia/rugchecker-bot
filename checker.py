from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "RugChecker API v4.1",
        "status": "online",
        "note": "Powered by DexScreener - no API key needed",
        "supported_chains": ["solana", "base", "ethereum"]
    })

@app.route('/status')
def status():
    return jsonify({"status": "ok", "service": "RugChecker v4.1"})

@app.route('/check')
def check_token():
    address = request.args.get('address')
    chain = request.args.get('chain', 'solana')

    if not address:
        return jsonify({"error": "Missing 'address' parameter"}), 400

    url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("pairs") and len(data["pairs"]) > 0:
            pairs = sorted(data["pairs"], key=lambda x: float(x.get("liquidity", {}).get("usd", 0)), reverse=True)
            pair = pairs[0]

            return jsonify({
                "contract_address": address,
                "chain": chain,
                "token_name": pair.get("baseToken", {}).get("name"),
                "token_symbol": pair.get("baseToken", {}).get("symbol"),
                "price_usd": float(pair.get("priceUsd", 0)),
                "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0)),
                "fdv": float(pair.get("fdv", 0)),
                "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
                "dex": pair.get("dexId"),
                "pair_address": pair.get("pairAddress"),
                "verified": True
            })
        else:
            return jsonify({
                "contract_address": address,
                "chain": chain,
                "error": "No trading pairs found",
                "reason": "Token has no liquidity or address is wrong"
            }), 404

    except Exception as e:
        return jsonify({"error": "Internal error", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
