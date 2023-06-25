from waitress import serve
from flask import Flask, jsonify, request, send_from_directory
import requests


class HederaPlugin:

  # Define the constructor for the class
  def __init__(self, base_url):
    # Initialize the base_url attribute
    self.base_url = base_url

  # Define methods to get the account balance
  def get_hbar_balance(self, account_id):
    # Define the endpoint for the balance API
    endpoint = "/balances"

    # Construct the full URL for the API request
    url = f"{self.base_url}{endpoint}?account.id={account_id}"

    balance_info = self.query_mirror_node_for(url)

    if balance_info is not None:
      # Iterate over the 'balances' in the response data
      for item in balance_info.get('balances', []):

        # Check if the account ID matches the requested account
        if item['account'] == account_id:

          # Calculate the HBAR balance and return it
          hBalance = float(item['balance']) * 1E-8
          return hBalance

    # Return None if the account or was not found
    return None

  def get_token_balance(self, account_id, token_id):
    # Define the endpoint for the balance API
    endpoint = "/balances"

    # Construct the full URL for the API request
    url = f"{self.base_url}{endpoint}?account.id={account_id}"

    balance_info = self.query_mirror_node_for(url)

    if balance_info is not None:

      # Iterate over the 'balances' in the response data
      for item in balance_info.get('balances', []):

        # Check if the account ID matches the requested account
        if item['account'] == account_id:

          # Iterate over the 'tokens' in the item
          for token in item.get('tokens', []):

            # Check if the token ID matches the requested token
            if token['token_id'] == token_id:

              # Define the endpoint for the token info API
              endpoint2 = "/tokens"
              # Construct the full URL for the token info API request
              url2 = f"{self.base_url}{endpoint2}/{token_id}"

              tokenInfo = self.query_mirror_node_for(url2)

              if tokenInfo is not None:

                # Get the number of decimals for the token
                decimals = float(tokenInfo['decimals'])

                # Calculate the token balance and return it
                tBalance = float(token['balance']) / (10**decimals)

                return tBalance

      # Return None if the query is wrong or if the account or token was not found
      return None

  def query_mirror_node_for(self, url):
    # Make a GET request to the mirror node REST API
    info = requests.get(url)
    # Check if the response status code is 200 (OK)
    if info.status_code == 200:
      # Parse the token info JSON response data
      info_data = info.json()
      return info_data
    else:
      # Return None if mirror node query is wrong or unsuccessful
      return None


# Initialize the plugin with the mainnet base URL
plugin = HederaPlugin("https://mainnet-public.mirrornode.hedera.com/api/v1")

# Create the Flask web server
app = Flask(__name__)


@app.route('/get_hbar_balance', methods=['GET'])
def get_hbar_balance():
  # Use query parameter 'account_id' to specify the account ID
  account_id = request.args.get('account_id', '')
  hbar_balance = plugin.get_hbar_balance(account_id)
  if hbar_balance is not None:
    return jsonify({'account_id': account_id, 'hbar_balance': hbar_balance})
  else:
    return jsonify({
      'error':
      'Could not get the HBAR balance for this account. Some possible reasons: The account ID may be incorrect or the mirror query was unsuccessful.'
    }), 404


@app.route('/get_token_balance', methods=['GET'])
def get_token_balance():
  # Use query parameter 'account_id' to specify the account ID
  account_id = request.args.get('account_id', '')
  token_id = request.args.get('token_id', '')
  token_balance = plugin.get_token_balance(account_id, token_id)
  if token_balance is not None:
    return jsonify({'account_id': account_id, 'token_balance': token_balance})
  else:
    return jsonify({
      'error':
      'Could not get the token balance for this account. Some possible reasons: The account and token ID may not be associated, the entity IDs may be incorrect, or the mirror query was unsuccessful.'
    }), 404


@app.route("/.well-known/ai-plugin.json", methods=['GET'])
def serve_ai_plugin():
  return send_from_directory(app.root_path,
                             'ai-plugin.json',
                             mimetype='application/json')


@app.route("/openapi.yaml", methods=['GET'])
def serve_openapi_yaml():
  return send_from_directory(app.root_path,
                             'openapi.yaml',
                             mimetype='text/yaml')


if __name__ == "__main__":
  serve(app, host="0.0.0.0", port=5000)
