let userAddress = null;

document.getElementById("connect").onclick = async () => {
  const accounts = await window.ethereum.request({
    method: "eth_requestAccounts"
  });

  userAddress = accounts[0];
  document.getElementById("claim").disabled = false;

  document.getElementById("output").textContent = `Connected: ${userAddress}`;
};

document.getElementById("claim").onclick = async () => {
  const resp = await fetch("/api/faucet", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ wallet: userAddress })
  });

  const data = await resp.json();
  document.getElementById("output").textContent = JSON.stringify(data, null, 2);
};
