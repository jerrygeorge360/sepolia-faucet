# Sepolia Testnet ERC-20 Faucet

A web application for distributing ERC-20 test tokens on the Sepolia testnet. Users can connect their wallet and claim test tokens for development and testing purposes.

## Features

- **Multiple Token Support**: Supports various ERC-20 test tokens including USDC, USDT, DAI, WETH, WBTC, and LINK
- **Wallet Integration**: MetaMask wallet connection with automatic network switching to Sepolia
- **Rate Limiting**: Prevents abuse with time-based claiming restrictions per wallet
- **Responsive Design**: Clean, modern UI that works on desktop and mobile
- **Real-time Feedback**: Shows transaction status and provides helpful error messages

## Tech Stack

### Frontend
- **Vite**: Fast build tool and development server
- **Vanilla JavaScript**: No framework dependencies for simplicity
- **Web3 Libraries**: `viem` and `wagmi` for Ethereum interactions
- **Responsive CSS**: Mobile-first design approach

### Backend
- **Flask**: Lightweight Python web framework
- **Web3.py**: Python library for Ethereum interactions
- **Rate Limiting**: Custom implementation to prevent token abuse
- **Environment Variables**: Secure configuration management

### Deployment
- **Vercel**: Serverless deployment platform
- **Vercel Functions**: Backend API hosted as serverless functions
- **Static Hosting**: Frontend assets served from Vercel edge network

## Supported Tokens

| Token | Symbol | Amount | Contract Address |
|-------|--------|--------|------------------|
| Dai Stablecoin | DAI | 10 | 0xAd22b4EC8cdd8A803d0052632566F6334A04F1F3 |
| USD Coin | USDC | 10 | 0xcF9884827F587Cd9a0bDce33995B2333eE7e8285 |
| Tether | USDT | 10 | 0x1861BB06286aAb0fDA903620844b4Aef4894b719 |
| Wrapped Bitcoin | WBTC | 10 | 0x4267652AF61B4bE50A39e700ee2a160f42371f54 | 

## Setup

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Ethereum wallet (MetaMask recommended)
- Sepolia testnet ETH for gas fees

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
RPC_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
PRIVATE_KEY=your_wallet_private_key_here
FAUCET_ADDRESS=your_faucet_wallet_address_here
```

### Local Development

1. **Install Dependencies**:
   ```bash
   # Install frontend dependencies
   cd frontend
   npm install
   
   # Install backend dependencies
   cd ../backend
   pip install -r requirements.txt
   ```

2. **Build Frontend**:
   ```bash
   cd frontend
   npm run build
   ```

3. **Run Backend**:
   ```bash
   cd backend
   python app.py
   ```

4. **Access the Application**:
   - Open http://localhost:5000 in your browser
   - Connect your MetaMask wallet
   - Switch to Sepolia testnet if prompted
   - Select a token and claim your test tokens

### Deployment to Vercel

1. **Connect Repository**:
   - Fork this repository
   - Connect your GitHub repository to Vercel

2. **Configure Environment Variables**:
   - Add the same environment variables in Vercel dashboard
   - Go to Project Settings → Environment Variables

3. **Deploy**:
   - Push changes to main branch
   - Vercel will automatically build and deploy

## API Endpoints

### `POST /api/faucet`
Request test tokens for a wallet address.

**Request Body**:
```json
{
  "wallet": "0x1234567890123456789012345678901234567890",
  "token": "USDC"
}
```

**Response**:
```json
{
  "success": true,
  "txHash": "0xabcdef...",
  "message": "Successfully sent 10 USDC to your wallet"
}
```

### `GET /api/status`
Get faucet status and available tokens.

### `GET /health`
Health check endpoint for monitoring.

## Rate Limiting

- Each wallet can claim tokens once every 24 hours per token type
- Rate limiting is enforced server-side to prevent abuse
- Clear error messages inform users when they need to wait

## Development Notes

- Rate limiting can be temporarily disabled in `rate_limit.py` for testing by modifying the `check_rate_limit` function to always return `True`
- The application uses a simple nonce management strategy that may need improvement under high concurrent load
- Frontend build artifacts are automatically generated in `backend/static/` when running `npm run build` in the frontend directory
- For production use, consider adding input validation, transaction queuing, and balance monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Project Structure

```
faucet/
├── api/
│   └── index.py         # Vercel serverless function entry point
├── backend/
│   ├── app.py           # Main Flask application
│   ├── tokens.py        # Token addresses and configurations
│   ├── rate_limit.py    # Rate limiting implementation
│   ├── requirements.txt # Python dependencies
│   ├── static/          # Built frontend assets (generated)
│   └── .env            # Environment variables (not in git)
├── frontend/
│   ├── index.html      # Frontend UI
│   ├── main.js         # Web3 integration and wallet logic
│   ├── package.json    # Frontend dependencies
│   └── vite.config.js  # Build configuration
├── package.json        # Root package file
├── vercel.json         # Vercel deployment configuration
└── requirements.txt    # Root Python dependencies for Vercel
```

