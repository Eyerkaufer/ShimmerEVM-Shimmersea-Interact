# ShimmerEVM Smart Contract Interaction Script README

## Overview
This script provides a comprehensive interface for interacting with the ShimmerEVM of the IOTA testnet Shimmer. It includes functionalities such as token swapping, fetching oracle prices, approving token transactions, and harvesting rewards from a smart contract. The script primarily focuses on operations involving LUM and SMR (Shimmer) tokens.
It shouldn't be used in any productive environment. It just showcases how you could use some of the smart contracts functionalities on the ShimmerEVM.

## Requirements
- Python 3.x
- `web3.py` library
- Access to a ShimmerEVM node
- An Ethereum wallet with a public address and private key

## Configuration
Before running the script, ensure that the following environmental variables are set:
- `SHIMMEREVM_NODE_ADDRESS_SPYCE5`: URL of the ShimmerEVM node. Get a free one setup in less than 5 min via Spyce5: https://app.spyce5.com/
- `SHIMMEREVM_FIREFOX_DEV_PUBLIC_ADDRESS`: Your public Ethereum address.
- `SHIMMEREVM_FIREFOX_DEV_PRIVATEKEY`: Your private Ethereum key.

## Features
### Token Addresses and Decimals
- `TOKEN_ADDRESS_LUM`: Address of the LUM token contract.
- `TOKEN_ADDRESS_SMR`: Address of the SMR token contract.
- `LUM_DECIMALS`: Decimal precision for LUM.
- `SMR_DECIMALS`: Decimal precision for SMR.

### EthereumShimmerContract Class
A utility class for interacting with Ethereum smart contracts on ShimmerEVM. It allows building and sending transactions and encapsulates functions like `build_transaction` and `send_transaction`.

### Utility Functions
- `calculate_token_exchange`: Calculates the equivalent amount of target token for a given amount of source token.
- `normalize_price`: Normalizes a token price to a specific decimal precision.
- `approve_token`: Approves a smart contract to spend a specified amount of tokens.
- `truncate_to_upper_digits`: Truncates a number to retain only a specified number of upper digits.
- `shimmersea_harvest_all`: Interacts with a farming contract to harvest rewards.
- `shimmersea_get_oracle_price`: Fetches the oracle price of a specified token.
- `shimmersea_swap`: Executes a token swap operation on the ShimmerEVM blockchain.
- `check_transaction_status`: Checks the status of a transaction and prints its hash.

### Main Functionality
The script's main function (`main`) allows the user to choose between different tasks:
- `HARVEST_ALL`: Harvest rewards from a specified contract.
- `GET_PRICE`: Get the oracle price of LUM and SMR tokens.
- `SWAP_LUM_TO_SMR`: Swap LUM tokens for SMR tokens.

## Usage
1. Set up the required environmental variables.
2. Run the script and select the desired task.
3. Follow the prompts or output to complete the operation.

## Notes
- Ensure that your wallet has enough funds to cover transaction fees.
- The private key is handled securely and is not exposed or transmitted.
- Always verify transaction details before confirming operations in your wallet.

---

This README provides a high-level overview of the script's capabilities and usage. For detailed information about each function or class, refer to the inline comments within the script.