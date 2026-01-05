from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from web3 import Web3
from dotenv import load_dotenv
import os
import logging
from tokens import TOKENS
from rate_limit import check_rate_limit

load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FAUCET_ADDRESS = Web3.to_checksum_address(os.getenv("FAUCET_ADDRESS"))

# Log connection status with error handling
try:
    logger.info(f"Web3 connected: {w3.is_connected()}")
except Exception as e:
    logger.warning(f"Could not check connection status: {e}")

try:
    logger.info(f"Chain ID: {w3.eth.chain_id}")
except Exception as e:
    logger.warning(f"Could not get chain ID: {e}")

try:
    logger.info(f"Latest block: {w3.eth.block_number}")
except Exception as e:
    logger.warning(f"Could not get latest block (RPC limitation): {e}")

try:
    eth_balance = w3.eth.get_balance(FAUCET_ADDRESS) / 10**18
    logger.info(f"Faucet ETH balance: {eth_balance} ETH")
except Exception as e:
    logger.warning(f"Could not get ETH balance: {e}")

# ERC20 ABI (transfer and balanceOf)
erc20_abi = [{
    "constant": False,
    "inputs": [
        {"name": "_to", "type": "address"},
        {"name": "_value", "type": "uint256"}
    ],
    "name": "transfer",
    "outputs": [{"name": "", "type": "bool"}],
    "type": "function"
}, {
    "constant": True,
    "inputs": [
        {"name": "_owner", "type": "address"}
    ],
    "name": "balanceOf",
    "outputs": [{"name": "balance", "type": "uint256"}],
    "type": "function"
}]


@app.route("/api/faucet", methods=["POST"])
def faucet():
    data = request.json
    wallet = data.get("wallet")
    requested_token = data.get("token")

    logger.info(f"Faucet request received: wallet={wallet}, token={requested_token}")

    if not wallet:
        logger.warning("Faucet request missing wallet address")
        return jsonify({"error": "Missing wallet address"}), 400
    
    if not requested_token:
        logger.warning("Faucet request missing token selection")
        return jsonify({"error": "Missing token selection"}), 400

    if requested_token not in TOKENS:
        logger.warning(f"Invalid token requested: {requested_token}")
        return jsonify({"error": f"Invalid token: {requested_token}"}), 400

    wallet = Web3.to_checksum_address(wallet)

    # Rate limit per wallet per token
    rate_limit_key = f"{wallet}:{requested_token}"
    if not check_rate_limit(rate_limit_key):
        logger.warning(f"Rate limit exceeded for {wallet} requesting {requested_token}")
        return jsonify({"error": f"Rate limit reached for {requested_token}. Try again in 24h."}), 429

    try:
        token = TOKENS[requested_token]
        contract = w3.eth.contract(address=Web3.to_checksum_address(token["address"]), abi=erc20_abi)

        # Check token balance first
        try:
            token_balance = contract.functions.balanceOf(FAUCET_ADDRESS).call()
            logger.info(f"Faucet {requested_token} balance: {token_balance / 10**token['decimals']}")
        except Exception as balance_error:
            logger.warning(f"Could not check token balance: {balance_error}")

        amount = 10 * (10 ** token["decimals"])
        
        # Add small random delay to spread out rapid requests
        import time
        import random
        delay = random.uniform(0.1, 0.5)  # 100-500ms random delay
        logger.info(f"Adding {delay:.2f}s delay to spread out requests")
        time.sleep(delay)
        
        # Get nonce with improved retry logic for rapid transactions
        max_retries = 5
        base_delay = 0.2  # Start with 200ms delay
        
        for retry in range(max_retries):
            try:
                # Use 'pending' to include pending transactions in nonce calculation
                nonce = w3.eth.get_transaction_count(FAUCET_ADDRESS, 'pending')
                logger.info(f"Got nonce {nonce} for transaction (attempt {retry + 1})")
                
                # Small delay to avoid rapid-fire nonce collisions
                if retry > 0:
                    import time
                    delay = base_delay * (2 ** retry)  # Exponential backoff
                    logger.info(f"Waiting {delay}s before retry...")
                    time.sleep(delay)
                
                break
            except Exception as nonce_error:
                if retry == max_retries - 1:
                    logger.error(f"Failed to get nonce after {max_retries} attempts: {nonce_error}")
                    raise nonce_error
                logger.warning(f"Nonce fetch failed (attempt {retry + 1}/{max_retries}): {nonce_error}")
                
                import time
                delay = base_delay * (2 ** retry)
                time.sleep(delay)

        logger.info(f"Building transaction: amount={amount}, nonce={nonce}")

        # Check if we have enough tokens
        try:
            token_balance = contract.functions.balanceOf(FAUCET_ADDRESS).call()
            if token_balance < amount:
                logger.error(f"Insufficient token balance: have {token_balance / 10**token['decimals']}, need {amount / 10**token['decimals']}")
                return jsonify({"error": f"Faucet doesn't have enough {requested_token} tokens"}), 500
        except Exception as balance_error:
            logger.warning(f"Could not verify token balance: {balance_error}")

        tx = contract.functions.transfer(wallet, amount).build_transaction({
            "from": FAUCET_ADDRESS,
            "nonce": nonce,
            "gas": 120000,
            "gasPrice": w3.to_wei("20", "gwei"),  # Increased gas price
            "chainId": 11155111  # Sepolia chain ID
        })

        logger.info(f"Transaction built successfully: {tx}")
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        logger.info(f"Transaction signed, sending to network...")
        
        # Handle both old and new Web3.py versions
        raw_tx = getattr(signed_tx, 'raw_transaction', getattr(signed_tx, 'rawTransaction', None))
        if raw_tx is None:
            raise Exception("Could not get raw transaction data")
        
        # Send transaction with retry logic for "already known" errors
        max_tx_retries = 3
        for tx_retry in range(max_tx_retries):
            try:
                tx_hash = w3.eth.send_raw_transaction(raw_tx)
                logger.info(f"Transaction sent successfully on attempt {tx_retry + 1}")
                logger.info(f"Raw tx_hash type: {type(tx_hash)}, value: {tx_hash}")
                break
            except Exception as send_error:
                error_msg = str(send_error).lower()
                if ("already known" in error_msg or "could not replace" in error_msg or "nonce too low" in error_msg) and tx_retry < max_tx_retries - 1:
                    logger.warning(f"Transaction collision detected (attempt {tx_retry + 1}): {send_error}")
                    logger.info("Regenerating transaction with new nonce...")
                    
                    # Get fresh nonce and rebuild transaction
                    import time
                    time.sleep(0.3)  # Small delay before retry
                    nonce = w3.eth.get_transaction_count(FAUCET_ADDRESS, 'pending')
                    logger.info(f"Rebuilding with fresh nonce: {nonce}")
                    
                    tx = contract.functions.transfer(wallet, amount).build_transaction({
                        "from": FAUCET_ADDRESS,
                        "nonce": nonce,
                        "gas": 120000,
                        "gasPrice": w3.to_wei("20", "gwei"),
                        "chainId": 11155111
                    })
                    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
                    raw_tx = getattr(signed_tx, 'raw_transaction', getattr(signed_tx, 'rawTransaction', None))
                    continue
                else:
                    logger.error(f"Transaction send failed after {tx_retry + 1} attempts: {send_error}")
                    raise send_error

        # Ensure transaction hash is properly formatted with 0x prefix
        if hasattr(tx_hash, 'hex'):
            tx_hash_str = tx_hash.hex()
        elif isinstance(tx_hash, bytes):
            tx_hash_str = tx_hash.hex()
        else:
            tx_hash_str = str(tx_hash)
        
        # Ensure it starts with 0x
        if not tx_hash_str.startswith('0x'):
            tx_hash_str = '0x' + tx_hash_str
        
        # Validate hash format (should be 66 characters: 0x + 64 hex chars)
        if len(tx_hash_str) != 66 or not all(c in '0123456789abcdefABCDEF' for c in tx_hash_str[2:]):
            logger.warning(f"Invalid transaction hash format: {tx_hash_str}")
            
        logger.info(f"Successfully sent {amount} {requested_token} to {wallet}, tx_hash: {tx_hash_str}")
        logger.info(f"Etherscan URL: https://sepolia.etherscan.io/tx/{tx_hash_str}")

        return jsonify({
            "message": f"Successfully sent 10 {requested_token} tokens",
            "token": requested_token,
            "amount": 10,
            "tx_hash": tx_hash_str,
            "wallet": wallet,
            "etherscan_url": f"https://sepolia.etherscan.io/tx/{tx_hash_str}"
        })

    except Exception as e:
        logger.error(f"Transaction failed for {wallet} requesting {requested_token}: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Error response: {e.response}")
        return jsonify({"error": f"Transaction failed: {str(e)}"}), 500


@app.route("/")
def index():
    return send_file('static/index.html')

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory('static', path)

@app.route("/api/status")
def api_status():
    return jsonify({"status": "Faucet backend running"})

@app.route("/api/admin/rate-limit/<wallet>", methods=["GET"])
def check_wallet_rate_limit(wallet):
    """Admin endpoint to check rate limit status for a wallet"""
    try:
        from rate_limit import get_rate_limit_status
        is_limited, remaining_seconds = get_rate_limit_status(wallet)
        
        if is_limited:
            hours = remaining_seconds // 3600
            minutes = (remaining_seconds % 3600) // 60
            return jsonify({
                "wallet": wallet,
                "rate_limited": True,
                "remaining_seconds": remaining_seconds,
                "remaining_time": f"{hours}h {minutes}m",
                "message": f"Rate limit active. Try again in {hours}h {minutes}m."
            })
        else:
            return jsonify({
                "wallet": wallet,
                "rate_limited": False,
                "message": "No rate limit active for this wallet."
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Starting faucet application on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Faucet address: {FAUCET_ADDRESS}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
