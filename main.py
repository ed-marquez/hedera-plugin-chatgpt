from waitress import serve
from flask import Flask, jsonify, request, send_from_directory
import requests


class HederaPlugin:

  def __init__(self, base_url):
    self.base_url = base_url

  def get_account_balance(self, account_id, token_id):
    endpoint = "/api/v1/balances"
    url = f"{self.base_url}{endpoint}?account.id={account_id}"
    response = requests.get(url)

    if response.status_code == 200:
      response_data = response.json()
      for item in response_data.get('balances', []):
        if item['account'] == account_id:
          if token_id == '':
            hBalance = float(item['balance']) * 1E-8
            return hBalance
          
          else:
            for token in item.get('tokens', []):
              if token['token_id'] == token_id:
                
                endpoint2 = "/api/v1/tokens"
                url2 = f"{self.base_url}{endpoint2}/{token_id}"
                tInfo = requests.get(url2)
                if tInfo.status_code == 200:
                  tInfo_data = tInfo.json()
                  decimals = float(tInfo_data['decimals'])
                
                  tBalance = float(token['balance']) / (10 ** decimals)

                return tBalance

    return None


# Initialize the plugin with the mainnet base URL
plugin = HederaPlugin("https://mainnet-public.mirrornode.hedera.com")

# Create the Flask web server
app = Flask(__name__)


@app.route('/get_account_balance', methods=['GET'])
def get_balance():
  # Use query parameter 'account_id' to specify the account ID
  account_id = request.args.get('account_id', '')
  token_id = request.args.get('token_id', '')
  balance = plugin.get_account_balance(account_id, token_id)

  if balance is not None:
    return jsonify({'account_id': account_id, 'balance': balance})
  else:
    return jsonify({'error': 'Could not fetch account balance.'}), 404


@app.route("/.well-known/ai-plugin.json", methods=['GET'])
def serve_ai_plugin():
  return send_from_directory(app.root_path,
                             'ai-plugin.json',
                             mimetype='application/json')


@app.route("/.well-known/openapi.yaml", methods=['GET'])
def serve_openapi_yaml():
  return send_from_directory(app.root_path,
                             'openapi.yaml',
                             mimetype='text/yaml')


if __name__ == "__main__":
  serve(app, host="0.0.0.0", port=5000)
