from waitress import serve
from flask import Flask, jsonify, request, send_from_directory
import requests
import time
import json
import os

class HederaPlugin:
  # Define the constructor for the class
  def __init__(self, base_url):
    # Initialize the base_url attribute
    self.base_url = base_url

  def get_hbar_balance(self, account_id):
    url = self._get_url("/balances", account_id=account_id)
    balance_info = self._query_mirror_node_for(url)

    if balance_info is not None:
      for item in balance_info.get('balances', []):
        if item['account'] == account_id:
          hBalance = float(item['balance']) * 1E-8
          return hBalance

    return None

  def get_single_token_balance(self, account_id, token_id):
    associationStatus = None
    tBalance = None
    url = self._get_url("/balances", account_id=account_id)
    balance_info = self._query_mirror_node_for(url)

    if balance_info is not None:
      for item in balance_info.get('balances', []):
        if item['account'] == account_id:
          for token in item.get('tokens', []):
            if token['token_id'] == token_id:
              associationStatus = True
              token_info_url = self._get_url(f"/tokens/{token_id}")
              token_info = self._query_mirror_node_for(token_info_url)
              if token_info is not None:
                decimals = float(token_info['decimals'])
                tBalance = float(token['balance']) / (10**decimals)
                return associationStatus, tBalance
            else:
              associationStatus = False
              tBalance = 0

    return associationStatus, tBalance

  def get_all_tokens_list(self, account_id):
    url = self._get_url("/balances", account_id=account_id)
    balance_info = self._query_mirror_node_for(url)

    tokenList = []
    if balance_info is not None:
      for item in balance_info.get('balances', []):
        if item['account'] == account_id:
          tokens = item.get('tokens', [])
          for token in tokens:
            token_info_url = self._get_url(f"/tokens/{token['token_id']}")
            token_info = self._query_mirror_node_for(token_info_url)
            if token_info is not None:
              tokenList.append({
                'token_id': token['token_id'],
                'token_name': token_info['name'],
                'token_symbol': token_info['symbol'],
                'balance': token['balance'],
                'token_type': token_info['type']
              })
      return tokenList
    return None

  def get_transactions_per_second(self):
    numBlocks = 5
    url = self._get_url(f"/blocks?limit={numBlocks}")
    response = self._query_mirror_node_for(url)
    if response is not None:
      blocks = response['blocks']
      sum_of_transactions = sum(block['count'] for block in blocks)

      newest_block_to_timestamp = float(blocks[0]['timestamp']['to'])
      oldest_block_from_timestamp = float(blocks[-1]['timestamp']['from'])
      duration = newest_block_to_timestamp - oldest_block_from_timestamp

      if duration > 0:
        transactions_per_second = sum_of_transactions / duration
        return transactions_per_second
    return None

  def get_nfts_minted_last_x_days(self, numDays):
    if float(numDays) < 1:
      numDays = 1

    hgraph_query = self._get_hgraph_query("GetNftsMintedByDay",
                                          numDays=numDays)
    data = self._get_hgraph_data(hgraph_query)

    nfts_minted_per_day = data['data']['nfts_minted_per_day']

    total_nfts_minted = sum(day['count'] for day in nfts_minted_per_day)
    return total_nfts_minted

  def get_nfts_minted_last_x_hours(self, num_hours):
    if float(num_hours) > 24:
      num_hours = 24

    time_window_in_seconds = num_hours * 3600
    now_in_seconds = time.time()
    start_in_seconds = now_in_seconds - time_window_in_seconds

    base_url = "https://mainnet-public.mirrornode.hedera.com"

    # Initialize the URL for the first page
    url = f"{base_url}/api/v1/transactions?transactionType=TOKENMINT&limit=100&timestamp=gt:{start_in_seconds}"

    # Initialize a list to store all transactions
    all_transactions = []

    while url:
      response = requests.get(url)
      data = response.json()

      # Add the transactions on the current page to the list
      all_transactions.extend(data['transactions'])

      # Get the URL for the next page
      url = data['links'].get('next')
      if url:
        url = f"{base_url}{url}"

    # Initialize counters for NFTs and fungible tokens
    nft_count = 0

    # Process all transactions
    for transaction in all_transactions:
      if transaction['result'] == 'SUCCESS':
        if 'nft_transfers' in transaction:
          # If the transaction has a 'token_transfers' field, it's a fungible token mint
          nft_count += len(transaction['nft_transfers'])

    return nft_count


  # ########################################################################
  # # TO BE ADDED IN LATER VERSION
  # ########################################################################
  # def get_nft_serials_of_X_owned_by_Y(self, accountId, tokenId):
  #   ########################################################################
  #   ## THIS QUERY WORKS IN THE PLAYGROUND TOOL, BUT NOT WITH THE API!
  #   ## ONCE HGRAPH.IO FIXES IT, JUST NEED TO MAKE IT A LITERAL STRING TO WORK WITH VARS
  #   ########################################################################
    
  #   hgraph_query = self._get_hgraph_query("GetSerialsOfNftXOwnedByY",
  #                                         accountId=accountId,
  #                                         tokenId=tokenId)
  #   data = self._get_hgraph_data(hgraph_query)

  #   info = data

  #   return data


# UTILITY FUNCTIONS
  def _get_url(self, endpoint, token_id=None, account_id=None):
    url = f"{self.base_url}{endpoint}"
    if token_id is not None:
      url += f"?token.id={token_id}"
    if account_id is not None:
      url += f"?account.id={account_id}"
    return url

  def _query_mirror_node_for(self, url):
    info = requests.get(url)
    if info.status_code == 200:
      return info.json()
    else:
      return None

  def _get_hgraph_data(self, query):
    endpoint = 'https://beta.api.hgraph.io/v1/graphql'
    headers = {
      'content-type': 'application/json',
      'x-api-key': os.getenv('HGRAPH_SECRET'),
    }
    response = requests.post(endpoint, headers=headers, data=json.dumps(query))
    data = response.json()
    return data

  def _get_hgraph_query(self,
                        q_name,
                        numDays=None,
                        accountId=None,
                        tokenId=None):

    if q_name == "GetNftsMintedByDay":
      hgraph_query = {
        "operationName":
        "GetNftsMintedByDay",
        "query":
        f"""
                query GetNftsMintedByDay {{
                    nfts_minted_per_day(limit: {numDays}, order_by: {{starting_at: desc}}) {{
                        count
                        ending_at
                        starting_at
                    }}
                }}
            """
      }

    # if q_name == "GetSerialsOfNftXOwnedByY": 
    #   # ########################################################################
    #   # THIS QUERY WORKS IN THE PLAYGROUND TOOL, BUT NOT WITH THE API! ADD IN LATER VERSION
    #   # ONCE HGRAPH.IO FIXES IT, JUST NEED TO MAKE IT A LITERAL STRING TO WORK WITH VARS
    #   # ########################################################################

    #   accountId = accountId.split(".")[-1]
    #   tokenId = tokenId.split(".")[-1]
    #   hgraph_query = {
    #       "operationName": "GetSerialsOfNftXOwnedByY",
    #       "query": 
    #       """
    #           query GetSerialsOfNftXOwnedByY {
    #             token_account(
    #               where: {account_id: {_eq: "505279"}, token: {token_id: {_eq: "1000808"}, type: {_eq: "NON_FUNGIBLE_UNIQUE"}
    #               }
    #               }
    #             ) {
    #               token {
    #                 token_id
    #                 name
    #                 symbol
    #               }
    #               associated
    #               balance
    #               nft {
    #                 serial_number
    #               }
    #             }
    #           }
    #       """
    #   }

    # if q_name == "GetSerialsOfAllNftsOwnedByX":
    #   # ########################################################################
    #   # THIS QUERY WORKS IN THE PLAYGROUND TOOL, BUT NOT WITH THE API! ADD IN LATER VERSION
    #   # ONCE HGRAPH.IO FIXES IT, JUST NEED TO MAKE IT A LITERAL STRING TO WORK WITH VARS
    #   # ########################################################################
    #   accountId = accountId.split(".")[-1]
    #   hgraph_query = {
    #     "operationName":
    #     "GetSerialsOfAllNftsOwnedByX",
    #     "query":
    #     f"""
    #           query GetSerialsOfNftXOwnedByY {{
    #               token_account(
    #                   where: {{account_id: {{_eq: \"{accountId}\"}}, token: {{type: {{_eq: \"NON_FUNGIBLE_UNIQUE\"}}}}}}
    #               ) {{
    #                   account_id
    #                   token {{
    #                       token_id
    #                       name
    #                       symbol
    #                   }}
    #                   associated
    #                   balance
    #                   nft {{
    #                       serial_number
    #                   }}
    #               }}
    #           }}
    #       """
    #   }

    return hgraph_query



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

@app.route('/get_single_token_balance', methods=['GET'])
def get_single_token_balance():
  # Use query parameter 'account_id' to specify the account ID
  account_id = request.args.get('account_id', '')
  token_id = request.args.get('token_id', '')
  association_status, token_balance = plugin.get_single_token_balance(
    account_id, token_id)
  if association_status or token_balance is not None:
    return jsonify({
      'association_status': association_status,
      'token_balance': token_balance
    })
  else:
    return jsonify({
      'error':
      'Could not get the token balance for this account. Some possible reasons: The account ID may be incorrect, or the mirror query was unsuccessful.'
    }), 404

@app.route('/get_all_tokens_list', methods=['GET'])
def get_all_tokens_list():
  # Use query parameter 'account_id' to specify the account ID
  account_id = request.args.get('account_id', '')
  token_list = plugin.get_all_tokens_list(account_id)
  if token_list is not None:
    return jsonify({'token_list': token_list})
  else:
    return jsonify({
      'error':
      'Could not get the list of tokens for this account. Some possible reasons: The account ID may be incorrect or the mirror query was unsuccessful.'
    }), 404

@app.route('/get_transactions_per_second', methods=['GET'])
def get_transactions_per_second():
  tps = plugin.get_transactions_per_second()
  if tps is not None:
    return jsonify({'transactions_per_second': tps})
  else:
    return jsonify({
      'error':
      'Could not get the Hedera TPS at this moment. Some possible reasons: The mirror query was unsuccessful.'
    }), 404

@app.route('/get_nfts_minted_last_x_days', methods=['GET', 'POST'])
def get_nfts_minted_last_x_days():
  num_days = request.args.get('num_days', '')
  nfts_minted_last_x_days = plugin.get_nfts_minted_last_x_days(num_days)
  if nfts_minted_last_x_days is not None:
    return jsonify({'nfts_minted_last_x_days': nfts_minted_last_x_days})
  else:
    return jsonify(
      {'error':
       'Could not get the number of NFTs minted at this moment.'}), 404

@app.route('/get_nfts_minted_last_x_hours', methods=['GET', 'POST'])
def get_nfts_minted_last_x_hours():
  num_hours = request.args.get('num_hours', '')
  nfts_minted_last_x_hours = plugin.get_nfts_minted_last_x_hours(num_hours)
  if nfts_minted_last_x_hours is not None:
    return jsonify({'nfts_minted_last_x_hours': nfts_minted_last_x_hours})
  else:
    return jsonify(
      {'error':
       'Could not get the number of NFTs minted at this moment.'}), 404
  
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
