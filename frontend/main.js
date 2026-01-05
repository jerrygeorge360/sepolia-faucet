let userAddress = null;

// Alert management functions
function showAlert(type, message, autoHide = false) {
  // Hide all alerts first
  hideAllAlerts();
  
  const alertId = `alert-${type}`;
  const messageId = `${type}-message`;
  
  document.getElementById(messageId).innerHTML = message;
  document.getElementById(alertId).classList.add('show');
  
  // Only auto-hide if specifically requested (for minor notifications)
  if (autoHide) {
    setTimeout(() => hideAlert(alertId), 5000);
  }
}

function hideAlert(alertId) {
  document.getElementById(alertId).classList.remove('show');
}

function hideAllAlerts() {
  document.querySelectorAll('.alert').forEach(alert => {
    alert.classList.remove('show');
  });
}

window.hideAlert = hideAlert;

// Wallet status management
function updateWalletDisplay() {
  const walletStatus = document.getElementById('wallet-status');
  const walletAddressEl = document.getElementById('wallet-address');
  
  if (userAddress) {
    walletAddressEl.textContent = userAddress;
    walletStatus.classList.add('connected');
  } else {
    walletStatus.classList.remove('connected');
  }
}

// Loading state management
function setLoadingState(isLoading) {
  const container = document.querySelector('.container');
  const claimButton = document.getElementById('claim');
  
  if (isLoading) {
    container.classList.add('loading');
    claimButton.textContent = 'Processing...';
    claimButton.disabled = true;
  } else {
    container.classList.remove('loading');
    claimButton.textContent = 'Claim 10 Tokens';
    updateClaimButton(); // Restore proper button state
  }
}

// Function to copy address to clipboard
window.copyAddress = async (address) => {
  try {
    await navigator.clipboard.writeText(address);
    // Show feedback
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    button.style.backgroundColor = '#218838';
    
    setTimeout(() => {
      button.textContent = originalText;
      button.style.backgroundColor = '#28a745';
    }, 2000);
    
    // Also show a brief success alert
    showAlert('success', `📋 Address copied to clipboard: ${address.slice(0, 10)}...${address.slice(-8)}`, true);
  } catch (err) {
    console.error('Failed to copy: ', err);
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = address;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    setTimeout(() => {
      button.textContent = originalText;
    }, 2000);
    
    showAlert('success', `📋 Address copied to clipboard: ${address.slice(0, 10)}...${address.slice(-8)}`, true);
  }
};

// Check if wallet is connected and token is selected to enable claim button
function updateClaimButton() {
  const tokenSelect = document.getElementById("token-select");
  const claimButton = document.getElementById("claim");
  
  claimButton.disabled = !userAddress || !tokenSelect.value;
}

// Handle token selection change
document.getElementById("token-select").addEventListener("change", () => {
  hideAllAlerts(); // Hide alerts when user changes selection
  updateClaimButton();
});

document.getElementById("connect").onclick = async () => {
  try {
    if (!window.ethereum) {
      showAlert('error', 'Please install MetaMask to connect your wallet.');
      return;
    }

    const accounts = await window.ethereum.request({
      method: "eth_requestAccounts"
    });

    userAddress = accounts[0];
    updateClaimButton();
    updateWalletDisplay();
    hideAllAlerts();

    showAlert('success', '🎉 Wallet connected successfully! Select a token and click claim.');
    document.getElementById("output").textContent = "Ready to claim tokens. Select a token from the dropdown above.";
  } catch (error) {
    console.error('Wallet connection failed:', error);
    showAlert('error', `Connection failed: ${error.message}`);
  }
};

document.getElementById("claim").onclick = async () => {
  const tokenSelect = document.getElementById("token-select");
  const selectedToken = tokenSelect.value;

  if (!selectedToken) {
    showAlert('warning', 'Please select a token first.');
    return;
  }

  if (!userAddress) {
    showAlert('warning', 'Please connect your wallet first.');
    return;
  }

  try {
    hideAllAlerts();
    setLoadingState(true);
    
    document.getElementById("output").textContent = `Claiming ${selectedToken} tokens...\nPlease wait while we process your request...`;
    
    const resp = await fetch("/api/faucet", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ 
        wallet: userAddress,
        token: selectedToken 
      })
    });

    const data = await resp.json();
    
    if (resp.ok) {
      // Validate transaction hash format
      const txHash = data.tx_hash;
      let etherscanUrl;
      
      if (txHash && txHash.length === 66 && txHash.startsWith('0x')) {
        // Use provided etherscan URL or construct it
        etherscanUrl = data.etherscan_url || `https://sepolia.etherscan.io/tx/${txHash}`;
      } else {
        console.warn('Invalid transaction hash format:', txHash);
        etherscanUrl = '#'; // Fallback to prevent broken links
      }
      
      const successMessage = `
        <strong style="font-size: 18px;">🎉 Tokens Successfully Claimed!</strong><br><br>
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">
          <strong>Token:</strong> ${selectedToken}<br>
          <strong>Amount:</strong> 10 ${selectedToken}<br>
          <strong>Recipient:</strong> <code style="font-size: 11px;">${userAddress}</code><br>
          <strong>Transaction:</strong> <code style="font-size: 11px; word-break: break-all;">${txHash}</code>
        </div>
        ${etherscanUrl !== '#' ? 
          `<div style="text-align: center; margin: 15px 0;">
            <a href="${etherscanUrl}" target="_blank" style="display: inline-block; background-color: #155724; color: white; padding: 8px 16px; border-radius: 5px; text-decoration: none; font-weight: bold;">
              📊 View Transaction on Etherscan
            </a>
          </div>` : 
          '<div style="color: #856404; text-align: center; margin: 10px 0;"><em>⚠️ Transaction hash format validation failed. Please check the backend logs.</em></div>'
        }
        <div style="background-color: #d1ecf1; padding: 8px; border-radius: 3px; margin-top: 10px;">
          <small><strong>💡 Next Steps:</strong><br>
          • Your tokens should appear in your wallet within 1-2 minutes<br>
          • If you don't see them, add the token contract address to MetaMask (see below)<br>
          • This alert will stay visible until you close it manually</small>
        </div>
      `;
      
      showAlert('success', successMessage);
      document.getElementById("output").textContent = `✅ Success! Your ${selectedToken} tokens have been sent.\n\nTransaction Hash: ${txHash}\n\nThe tokens should appear in your wallet soon. If you don't see them, add the token to MetaMask using the contract address shown below.`;
    } else {
      const errorMessage = data.error || 'Failed to claim tokens';
      
      // Handle rate limiting specifically
      if (resp.status === 429) {
        showAlert('warning', `⏰ ${errorMessage}<br><br><small>Each wallet can claim each token once per 24 hours. This helps ensure fair distribution of testnet tokens.</small>`);
      } else {
        showAlert('error', `❌ ${errorMessage}`);
      }
      
      document.getElementById("output").textContent = `❌ Error: ${errorMessage}`;
    }
  } catch (error) {
    console.error('Claim request failed:', error);
    showAlert('error', `❌ Request failed: ${error.message}`);
    document.getElementById("output").textContent = `❌ Request failed: ${error.message}`;
  } finally {
    setLoadingState(false);
  }
};

// Wallet event listeners and initialization
if (window.ethereum) {
  // Listen for account changes
  window.ethereum.on('accountsChanged', (accounts) => {
    if (accounts.length === 0) {
      // User disconnected wallet
      userAddress = null;
      updateWalletDisplay();
      updateClaimButton();
      hideAllAlerts();
      showAlert('warning', '⚠️ Wallet disconnected. Please connect your wallet to claim tokens.');
      document.getElementById("output").textContent = "Wallet disconnected. Please connect your wallet to get started.";
    } else if (accounts[0] !== userAddress) {
      // User switched accounts
      userAddress = accounts[0];
      updateWalletDisplay();
      updateClaimButton();
      hideAllAlerts();
      showAlert('success', '🔄 Account switched successfully!', true);
      document.getElementById("output").textContent = "Account switched. Ready to claim tokens.";
    }
  });

  // Listen for chain changes
  window.ethereum.on('chainChanged', (chainId) => {
    // Reload the page when chain changes
    window.location.reload();
  });

  // Check if already connected on page load
  window.ethereum.request({ method: 'eth_accounts' })
    .then((accounts) => {
      if (accounts.length > 0) {
        userAddress = accounts[0];
        updateWalletDisplay();
        updateClaimButton();
        document.getElementById("output").textContent = "Wallet already connected. Select a token and click claim.";
      }
    })
    .catch(console.error);
}
