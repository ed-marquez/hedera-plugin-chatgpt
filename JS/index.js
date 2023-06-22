const express = require("express");
const axios = require("axios");
const app = express();
const path = require("path");

const baseURL = "https://mainnet-public.mirrornode.hedera.com";

async function getBalance(account_id, token_id) {
	try {
		let url = `${baseURL}/api/v1/balances?account.id=${account_id}`;
		let response = await axios.get(url);
		let balances = response.data.balances;
		for (let item of balances) {
			if (item.account === account_id) {
				if (token_id === "") {
					return parseFloat(item.balance) * 1e-8;
				} else {
					for (let token of item.tokens) {
						if (token.token_id === token_id) {
							let url2 = `${baseURL}/api/v1/tokens/${token_id}`;
							let tInfo = await axios.get(url2);
							let decimals = parseFloat(tInfo.data.decimals);
							return parseFloat(token.balance) / 10 ** decimals;
						}
					}
				}
			}
		}
	} catch (error) {
		console.log(error);
	}
	return null;
}

app.get("/get_account_balance", async (req, res) => {
	let account_id = req.query.account_id || "";
	let token_id = req.query.token_id || "";
	let balance = await getBalance(account_id, token_id);
	if (balance != null) {
		res.json({ account_id: account_id, balance: balance });
	} else {
		res.status(404).json({ error: "Could not fetch account balance." });
	}
});

app.get("/.well-known/ai-plugin.json", (req, res) => {
	res.sendFile(path.join(__dirname, "ai-plugin.json"));
});

app.get("/openapi.yaml", (req, res) => {
	res.sendFile(path.join(__dirname, "openapi.yaml"));
});

app.listen(5000, () => console.log("Server running on port 5000"));
