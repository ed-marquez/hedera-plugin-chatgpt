const express = require('express');
const axios = require('axios');
const path = require('path');
const app = express();
const port = 5000;

class HederaPlugin {
  constructor(base_url) {
    this.base_url = base_url;
  }

  async get_account_balance(account_id) {
    const endpoint = "/api/v1/balances";
    const url = `${this.base_url}${endpoint}?account.id=${account_id}`;

    try {
      const response = await axios.get(url);
      if (response.status === 200) {
        const response_data = response.data;
        for (const item of response_data.balances || []) {
          if (item.account === account_id) {
            const balance = parseFloat(item.balance) * 1E-8;
            return balance;
          }
        }
      }
    } catch (error) {
      console.error(error);
    }

    return null;
  }
}

// Initialize the plugin with the mainnet base URL
const plugin = new HederaPlugin("https://mainnet-public.mirrornode.hedera.com");

app.get('/get_account_balance', async (req, res) => {
  const account_id = req.query.account_id;
  const balance = await plugin.get_account_balance(account_id);

  if (balance !== null) {
    res.json({ account_id: account_id, balance: balance });
  } else {
    res.status(404).json({ error: 'Could not fetch account balance.' });
  }
});

app.get('/.well-known/ai-plugin.json', (req, res) => {
  res.sendFile(path.join(__dirname, 'ai-plugin.json'));
});

app.get('/.well-known/openapi.yaml', (req, res) => {
  res.sendFile(path.join(__dirname, 'openapi.yaml'));
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
