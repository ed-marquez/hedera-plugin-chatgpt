from waitress import serve
from flask import Flask, jsonify, request, send_from_directory
import requests


class HederaPlugin:

  # Define the constructor for the class
  def __init__(self, base_url):
    # Initialize the base_url attribute
    self.base_url = base_url

  # Define a method to get the account balance
  def get_account_balance(self, account_id, token_id):
    # Define the endpoint for the balance API
    endpoint = "/api/v1/balances"
    # Construct the full URL for the API request
    url = f"{self.base_url}{endpoint}?account.id={account_id}"
    # Make a GET request to the API
    response = requests.get(url)
    # Check if the response status code is 200 (OK)
    if response.status_code == 200:

      # Parse the JSON response data
      response_data = response.json()
      # Iterate over the 'balances' in the response data
      for item in response_data.get('balances', []):

        # Check if the account ID matches the requested account
        if item['account'] == account_id:

          # Check if the token ID is empty
          if token_id == '':

            # Calculate the HBAR balance and return it
            hBalance = float(item['balance']) * 1E-8
            return hBalance

          else:
            # Iterate over the 'tokens' in the item
            for token in item.get('tokens', []):

              # Check if the token ID matches the requested token
              if token['token_id'] == token_id:

                # Define the endpoint for the token info API
                endpoint2 = "/api/v1/tokens"
                # Construct the full URL for the token info API request
                url2 = f"{self.base_url}{endpoint2}/{token_id}"
                # Make a GET request to the token info API
                tInfo = requests.get(url2)
                # Check if the token info API response status code is 200 (OK)
                if tInfo.status_code == 200:

                  # Parse the token info JSON response data
                  tInfo_data = tInfo.json()
                  # Get the number of decimals for the token
                  decimals = float(tInfo_data['decimals'])
                  # Calculate the token balance and return it
                  tBalance = float(token['balance']) / (10**decimals)

                return tBalance

    # Return None if the account or token was not found
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


@app.route("/openapi.yaml", methods=['GET'])
def serve_openapi_yaml():
  return send_from_directory(app.root_path,
                             'openapi.yaml',
                             mimetype='text/yaml')


if __name__ == "__main__":
  serve(app, host="0.0.0.0", port=5000)
