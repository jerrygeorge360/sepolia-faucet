# Sepolia Faucet

Quick testnet token faucet for Sepolia. Connect your wallet, pick a token, get 10 of them. That's it.

## What it does

This faucet gives out DAI, USDC, USDT, and WBTC on Sepolia testnet. You get 10 tokens per request, once every 24 hours. Built with Flask + Web3.py on the backend and vanilla JS on the frontend.

Rate limiting works with Redis if you have it, otherwise just uses memory.

## Token addresses

- DAI: `0xAd22b4EC8cdd8A803d0052632566F6334A04F1F3` 
- USDC: `0xcF9884827F587Cd9a0bDce33995B2333eE7e8285` 
- USDT: `0x1861BB06286aAb0fDA903620844b4Aef4894b719` 
- WBTC: `0x4267652AF61B4bE50A39e700ee2a160f42371f54` 

## Running it

You need Python 3.9+, Node.js, and a wallet with some Sepolia ETH. The faucet wallet needs to already have tokens to give out.

```bash
git clone <repo-url>
cd faucet

# Frontend
cd frontend && npm install && cd ..

# Backend  
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

Create `backend/.env`:
```
RPC_URL=https://sepolia.drpc.org
PRIVATE_KEY=0x...
FAUCET_ADDRESS=0x...
REDIS_URL=redis://localhost:6379  # optional
```

Then run it:
```bash
npm start  # everything on localhost:5000
```

## How it works

Connect MetaMask, pick a token from the dropdown, click claim. Backend checks if you've already claimed that token in the last 24 hours, then sends it to your wallet if you haven't.

Pretty straightforward. The transaction hash gets returned so you can check it on Etherscan.

## Quirks and limitations

- Always sends exactly 10 tokens, no way to change this
- Only works on Sepolia (chain ID 11155111) 
- One token per request
- No admin interface for managing rate limits
- UI doesn't show faucet token balances
- Error messages could be better

## API

Main endpoint is `POST /api/faucet`:

```bash
curl -X POST http://localhost:5000/api/faucet \
  -H "Content-Type: application/json" \
  -d '{"wallet": "0x742d35Cc6597C1A0C91Bf0C1E87cBEd1C3Ce8A4C", "token": "USDC"}'
```

Returns either success with tx hash or rate limit error.

There's also `GET /api/admin/rate-limit/{wallet}` to check if someone is rate limited.

## Troubleshooting

Common problems:
- Transaction failed → faucet probably ran out of tokens or ETH
- Rate limit reached → wait 24 hours
- Missing wallet → connect MetaMask first
- Network errors → check if RPC is working

For development issues, rate limiting can be disabled in `rate_limit.py` (just return `True` from `check_rate_limit`).

## Notes

This was thrown together pretty quickly. There's no input validation, no transaction queuing, no balance monitoring. It works for basic testing but isn't production-grade by any stretch.

The nonce handling tries to deal with rapid requests but might still have issues under heavy load.

```
faucet/
├── backend/
│   ├── app.py           # main flask app
│   ├── tokens.py        # token addresses and decimals
│   ├── rate_limit.py    # rate limiting stuff
│   ├── requirements.txt 
│   └── .env            # your secrets go here
├── frontend/
│   ├── index.html      # the UI
│   ├── main.js         # web3 integration  
│   ├── package.json
│   └── vite.config.js
└── package.json        # root scripts
```

