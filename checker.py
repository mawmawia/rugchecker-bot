from flask import Flask, request, jsonify
from web3 import Web3
import csv
import os
from datetime import datetime

app = Flask(__name__)

print("LOADING V3.9.4 - BLACKLIST + FORCED CENTRALIZED CHECK")

RPC_LIST = [
    'https://rpc.ankr.com/eth',
    'https://eth.llamarpc.com', 
    'https://ethereum.publicnode.com',
    'https://1rpc.io/eth'
]

WHITELIST = {
    "0xdac17f958d2ee523a2206206994597c13d831ec7", # USDT
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", # USDC 
    "0x6b175474e89094c44da98b954eedeac495271d0f", # DAI
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", # WBTC
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", # WETH
    "0x514910771af9ca656af840dff83e8264ecf986ca", # LINK
    "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984", # UNI
    "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce" # SHIB
}

TAX_OVERRIDE = {
    "0x42981d0bfbaf196529376ee702f2a9eb9092fcb5": 10.0, # Safemoon v2
}

# Known honeypots/rugs - always RISKY regardless of sim
BLACKLIST = {
    "0x6982508145454ce325ddbe47a25d4ec3d2311933": "Confirmed honeypot",
}

def get_w3():
    for rpc in RPC_LIST:
        w3 = Web3(Web3.HTTPProvider(rpc))
        if w3.is_connected():
            print(f"Connected to {rpc}")
            return w3
    return None

ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"type":"function"}
]

ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"

def log_result(address, status, reason):
    file_exists = os.path.exists('token_log.csv')
    with open('token_log.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp','address','status','reason'])
        writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), address, status, reason])

@app.route('/check')
def check():
    address = request.args.get('address')
    w3 = get_w3()
    if not w3:
        return jsonify({"status": "RISKY", "reason": "RPC offline"})
    
    try:
        address = w3.to_checksum_address(address)
        address_lower = address.lower()
    except:
        return jsonify({"status": "RISKY", "reason": "Invalid address"})
    
    # BLACKLIST CHECK FIRST - OVERRIDES EVERYTHING
    if address_lower in BLACKLIST:
        reason = f"Blacklisted: {BLACKLIST[address_lower]}"
        print(f"BLACKLIST TRIGGERED: {reason}")
        log_result(address, "RISKY", reason)
        return jsonify({"status": "RISKY", "reason": reason})
    
    red_flags = []
    green_flags = []
    warnings = []
    
    is_whitelisted = address_lower in WHITELIST
    print(f"CHECK: {address} | Whitelisted: {is_whitelisted}")
    
    try:
        contract = w3.eth.contract(address=address, abi=ERC20_ABI)

        # 1. OWNER CHECK
        has_owner = False
        try:
            owner = contract.functions.owner().call()
            if owner == "0x0000000000000000":
                green_flags.append("Renounced")
            else:
                warnings.append("Owner active")
                has_owner = True
        except:
            green_flags.append("No owner")

        # 2. LIQUIDITY CHECK
        low_lp = False
        try:
            factory = w3.eth.contract(address=FACTORY, abi=[{"constant":True,"inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"}],"name":"getPair","outputs":[{"name":"pair","type":"address"}],"type":"function"}])
            pair = factory.functions.getPair(address, WETH).call()
            if pair == "0x0000000000000000":
                warnings.append("No V2 LP")
                low_lp = True
            else:
                lp_eth = w3.from_wei(w3.eth.get_balance(pair), 'ether')
                if lp_eth < 0.5:
                    warnings.append(f"Low V2 LP {lp_eth:.1f} ETH")
                    low_lp = True
                else:
                    green_flags.append(f"LP {lp_eth:.0f} ETH")
        except:
            warnings.append("LP unverified")
            low_lp = True

        # 3. TAX CHECK - OVERRIDE FIRST, >= 10% IS CRITICAL
        tax_found = False
        trade_sim_failed = False
        
        if address_lower in TAX_OVERRIDE:
            tax = TAX_OVERRIDE[address_lower]
            print(f"TAX OVERRIDE TRIGGERED: {tax}%")
            if tax >= 10:
                red_flags.append(f"Tax {tax}%")
            elif tax > 3:
                warnings.append(f"Tax {tax}%")
            else:
                green_flags.append(f"Tax {tax}%")
            tax_found = True
        
        if not tax_found:
            try:
                router = w3.eth.contract(address=ROUTER, abi=[{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"}])
                
                tokens = router.functions.getAmountsOut(w3.to_wei(0.01, 'ether'), [WETH, address]).call()[1]
                if tokens == 0:
                    red_flags.append("Honeypot")
                    trade_sim_failed = True
                else:
                    try:
                        eth_back = router.functions.getAmountsOut(tokens, [address, WETH]).call()[1]
                        if eth_back < w3.to_wei(0.01, 'ether'):
                            tax = round((w3.to_wei(0.01, 'ether') - eth_back) / w3.to_wei(0.01, 'ether') * 100, 1)
                            if tax >= 49:
                                red_flags.append(f"Honeypot {tax}%")
                            elif tax >= 10:
                                red_flags.append(f"Tax {tax}%")
                            elif tax > 3:
                                warnings.append(f"Tax {tax}%")
                            else:
                                green_flags.append(f"Tax {tax}%")
                        else:
                            green_flags.append("Tax 0%")
                    except:
                        trade_sim_failed = True
            except:
                trade_sim_failed = True
        
        if trade_sim_failed and not tax_found:
            if is_whitelisted:
                warnings.append("Trade restricted")
            else:
                red_flags.append("Trade blocked")
                print("TRADE BLOCKED - NOT WHITELISTED")

        # 4. CENTRALIZED + LOW LP CHECK - FORCED
        if not is_whitelisted and has_owner and low_lp:
            red_flags.append("Centralized + Low LP")
            print("CENTRALIZED + LOW LP TRIGGERED")

        # FINAL LOGIC
        critical_flags = ["Honeypot", "Trade blocked", "Tax", "Centralized + Low LP"] 
        is_critical = any(flag in " ".join(red_flags) for flag in critical_flags)
        
        print(f"FINAL: Critical={is_critical} | Red={red_flags} | Green={green_flags} | Warn={warnings}")
        
        if is_critical:
            reason = " | ".join(red_flags + warnings)
            log_result(address, "RISKY", reason)
            return jsonify({"status": "RISKY", "reason": reason})
        elif green_flags or is_whitelisted:
            reason = " | ".join(green_flags + warnings)
            log_result(address, "SAFE", reason)
            return jsonify({"status": "SAFE", "reason": reason})
        else:
            reason = " | ".join(red_flags + warnings) if red_flags or warnings else "Unverified"
            log_result(address, "RISKY", reason)
            return jsonify({"status": "RISKY", "reason": reason})

    except Exception as e:
        print(f"Error: {e}")
        log_result(address, "RISKY", "Invalid token")
        return jsonify({"status": "RISKY", "reason": "Invalid token"})

@app.route('/stats')
def stats():
    if not os.path.exists('token_log.csv'):
        return jsonify({"total": 0, "safe": 0, "risky": 0})
    with open('token_log.csv', 'r') as f:
        lines = f.readlines()[1:]
        total = len(lines)
        safe = sum(1 for line in lines if ',SAFE,' in line)
        risky = total - safe
    return jsonify({"total": total, "safe": safe, "risky": risky})

import os
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
