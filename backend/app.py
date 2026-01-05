from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from web3 import Web3
from dotenv import load_dotenv
import os
from tokens import TOKENS
from rate_limit import check_rate_limit

load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FAUCET_ADDRESS = Web3.to_checksum_address(os.getenv("FAUCET_ADDRESS"))

# ERC20 ABI (transfer)
erc20_abi = [{
    "constant": False,
    "inputs": [
        {"name": "_to", "type": "address"},
        {"name": "_value", "type": "uint256"}
    ],
    "name": "transfer",
    "outputs": [{"name": "", "type": "bool"}],
    "type": "function"
}]


@app.route("/api/faucet", methods=["POST"])
def faucet():
    data = request.json
    wallet = data.get("wallet")

    if not wallet:
        return jsonify({"error": "Missing wallet"}), 400

    wallet = Web3.to_checksum_address(wallet)

    # Rate limit
    if not check_rate_limit(wallet):
        return jsonify({"error": "Rate limit reached. Try again in 24h."}), 429

    results = []
    nonce = w3.eth.get_transaction_count(FAUCET_ADDRESS)

    for symbol, token in TOKENS.items():
        contract = w3.eth.contract(address=Web3.to_checksum_address(token["address"]), abi=erc20_abi)

        amount = 10 * (10 ** token["decimals"])

        tx = contract.functions.transfer(wallet, amount).build_transaction({
            "from": FAUCET_ADDRESS,
            "nonce": nonce,
            "gas": 120000,
            "gasPrice": w3.to_wei("3", "gwei")
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        nonce += 1

        results.append({
            "token": symbol,
            "tx_hash": tx_hash.hex()
        })

    return jsonify({
        "message": "Faucet sent 10 tokens each.",
        "results": results
    })


@app.route("/")
def index():
    return send_file('static/index.html')

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory('static', path)

@app.route("/api/status")
def api_status():
    return jsonify({"status": "Faucet backend running"})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
