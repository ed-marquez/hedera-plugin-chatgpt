from main import HederaPlugin

# Initialize the plugin with the mainnet base URL
plugin = HederaPlugin("https://mainnet-public.mirrornode.hedera.com/api/v1")

# ans = plugin.get_nfts_minted_last_x_days(3)

# 
# print("TEST 1")
# res1 = plugin.get_hbar_balance("0.0.505279")
# print(res1)
# print("")

# print("TEST 2")
# res2 = plugin.get_single_token_balance("0.0.505279", "0.0.731861")
# print(res2)
# print("")

# print("TEST 3")
# res3 = plugin.get_all_tokens_list("0.0.655928")
# print(res3)
# print("")

# print("TEST 4")
# res4 = plugin.get_transactions_per_second()
# print(res4)
# print("")

# print("TEST 5")
# res5 = plugin.get_nfts_minted_last_x_days(2)
# print(res5)
# print("")

print("TEST 6")
res6 = plugin.get_nfts_minted_last_x_hours(5)
print(res6)
print("")
