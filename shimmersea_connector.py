from web3 import Web3
import json
import os
import time
import shimmerevm_abi

######### ADDRESSES #########
TOKEN_ADDRESS_LUM = Web3.to_checksum_address('0x4794Aeafa5Efe2fC1F6f5eb745798aaF39A81D3e')  # LUM
LUM_DECIMALS = 18  # ether
TOKEN_ADDRESS_SMR = Web3.to_checksum_address('0x1074010000000000000000000000000000000000')  # SMR
SMR_DECIMALS = 6  # mwei

SHIMMERSEA_SWAP_SPENDER_ADDRESS = Web3.to_checksum_address('0x3edafd0258f75e0f49d570b1b28a1f7a042bcec3')


######### ADDRESSES END #########
SHIMMER_CHAIN_ID = 148
SHIMMER_GAS_PRICE = '1000'
SHIMMER_GAS_UPPER_LIMIT = 800000


class EthereumShimmerContract:
    def __init__(self, web3, address, abi):
        self.web3 = web3
        self.address = address
        self.contract = self.web3.eth.contract(address=self.address, abi=abi)

    def build_transaction(self, function_name, function_args, account, nonce, chain_id, gas, gas_price):
        if function_name not in [func['name'] for func in self.contract.abi if 'name' in func]:
            raise Exception(f"{function_name} function not found in ABI")

        function_call = getattr(self.contract.functions, function_name)(*function_args)
        transaction = function_call.build_transaction({
            'chainId': chain_id,
            'gas': gas,
            'gasPrice': self.web3.to_wei(gas_price, 'gwei'),
            'nonce': nonce,
        })
        return transaction

    def send_transaction(self, transaction, private_key):
        signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key)
        txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        txn_receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return txn_receipt


def check_transaction_status(txn_receipt):
    """
    Check the status of a transaction and print its hash.

    :param txn_receipt: The transaction receipt object.
    """
    # Check if the transaction receipt is valid
    if not txn_receipt:
        print("Invalid transaction receipt.")
        return

    # Extracting the status and transaction hash from the receipt
    status = txn_receipt.status
    txn_hash = txn_receipt.transactionHash.hex()  # Convert bytes to hex string

    # Check and print the status
    if status == 1:
        print(f"Transaction was successful. Transaction Hash: {txn_hash}")
    else:
        print(f"Transaction failed. Transaction Hash: {txn_hash}")
    return status

def calculate_token_exchange(token_price_from, token_price_to, amount, from_decimals=18, to_decimals=18):
    normalized_price_from = normalize_price(token_price_from, from_decimals)
    normalized_price_to = normalize_price(token_price_to, to_decimals)
    return (normalized_price_from * amount) / normalized_price_to


def normalize_price(price, token_decimals, target_decimals=18):
    standard_decimals = 18  # Standard in Ethereum. Of course SMR on ShimmerEVM has a different value (6) ...
    if token_decimals + target_decimals <= 2 * standard_decimals:
        return price / 10 ** (2 * standard_decimals - token_decimals - target_decimals)
    else:
        return price * 10 ** (target_decimals + token_decimals - 2 * standard_decimals)


def approve_token(web3, account, private_key, token_address, spender, amount, chain_id, gas, gas_price):
    token_contract = web3.eth.contract(address=token_address, abi=shimmerevm_abi.shimmersea_lum_token_abi_string)
    nonce = web3.eth.get_transaction_count(account)

    approve_txn = token_contract.functions.approve(spender, amount).build_transaction({
        'chainId': chain_id,
        'gas': gas,
        'gasPrice': web3.to_wei(gas_price, 'gwei'),
        'nonce': nonce,
    })

    signed_txn = web3.eth.account.sign_transaction(approve_txn, private_key)
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    txn_receipt = web3.eth.wait_for_transaction_receipt(txn_hash)
    return txn_receipt


def truncate_to_upper_digits(number, digits):
    """
    Truncate a number to keep only the upper specified number of digits.
    :param number: The number to be truncated.
    :param digits: The number of digits to retain.
    :return: The truncated number.
    """
    # Convert to integer to remove decimal places
    number = int(number)

    # Determine the number of digits in the number
    number_length = len(str(number))

    # If the number of digits required is greater than the length of the number, return the number
    if digits >= number_length:
        return number

    # Scale down the number to get the top 'digits' digits
    scale_down_factor = 10 ** (number_length - digits)
    return number // scale_down_factor


def shimmersea_harvest_all(web3, account, private_key, pids, chain_id, gas, gas_price):
    contract_address = Web3.to_checksum_address('0x686eAd3Fee35C811684E6158408B49220d912dD4')
    abi = json.loads(shimmerevm_abi.shimmersea_harvest_all_abi_string)
    ethereum_contract = EthereumShimmerContract(web3, contract_address, abi)
    nonce = ethereum_contract.web3.eth.get_transaction_count(account)
    txn = ethereum_contract.build_transaction(
        'harvestAll', [pids], account, nonce, chain_id, gas, gas_price
    )
    txn_receipt = ethereum_contract.send_transaction(txn, private_key)
    return txn_receipt


def shimmersea_get_oracle_price(web3, token_address, decimals=18):
    price_getter_contract_address = Web3.to_checksum_address('0xC0E5E2608E9779bFC14C0c632510E57982aFB63C')
    abi = json.loads(shimmerevm_abi.shimmersea_oracle_price_abi_string)
    contract = web3.eth.contract(address=price_getter_contract_address, abi=abi)
    price = contract.functions.getPrice(token_address, decimals).call()
    return price


def shimmersea_swap(web3, account, private_key, amount_in, amount_out_min, path, to, deadline, chain_id, gas, gas_price):
    contract_address = Web3.to_checksum_address('0x3EdAFd0258F75E0F49d570B1b28a1F7A042bcEC3')
    abi = json.loads(shimmerevm_abi.shimmersea_swap_abi_string)
    ethereum_contract = EthereumShimmerContract(web3, contract_address, abi)

    nonce = ethereum_contract.web3.eth.get_transaction_count(account)

    # Convert amount_in to Wei (if it's in Ether)
    # amount_in_wei = web3.to_wei(amount_in, 'ether')

    txn = ethereum_contract.build_transaction(
        'swapExactTokensForTokens',
        [amount_in, amount_out_min, path, to, deadline],
        account, nonce, chain_id, gas, gas_price
    )
    txn_receipt = ethereum_contract.send_transaction(txn, private_key)
    return txn_receipt


def main():
    TASK = 'SWAP_LUM_TO_SMR'

    provider_url = os.getenv('SHIMMEREVM_NODE_ADDRESS_SPYCE5')  # The node url
    my_account = os.getenv('SHIMMEREVM_FIREFOX_DEV_PUBLIC_ADDRESS')  # Public address
    private_key = os.getenv('SHIMMEREVM_FIREFOX_DEV_PRIVATEKEY')  # Get private key from environmental variable

    web3 = Web3(Web3.HTTPProvider(provider_url))
    if not web3.is_connected():
        raise Exception("Failed to connect to the Ethereum network")

    if private_key is None:
        raise ValueError("Private key not found in environment variables")

    if 'HARVEST_ALL' in TASK:
        pids = [1]  # Replace with actual pool IDs
        txn_receipt = shimmersea_harvest_all(web3, my_account, private_key, pids, 148, 800000, '1000')
        print(txn_receipt)
    elif 'GET_PRICE' in TASK:
        lum_amount = 0.24
        token_price_lum = shimmersea_get_oracle_price(web3, TOKEN_ADDRESS_LUM)
        token_price_smr = shimmersea_get_oracle_price(web3, TOKEN_ADDRESS_SMR, 6)

        print(f"Price of the LUM token: {token_price_lum} (normalized to 18 decimals)")
        print(f"Price of the SMR token: {token_price_smr} (normalized to 6 decimals)")

        smr_equivalent = calculate_token_exchange(token_price_lum, token_price_smr, lum_amount)
        print(f"{lum_amount} LUM is equivalent to {smr_equivalent} SMR")

    elif 'SWAP_LUM_TO_SMR' in TASK:
        lum_amount = 0.00001

        token_price_lum = shimmersea_get_oracle_price(web3, TOKEN_ADDRESS_LUM)
        token_price_smr = shimmersea_get_oracle_price(web3, TOKEN_ADDRESS_SMR, SMR_DECIMALS)
        print(f"Token price smr: {token_price_smr}")
        smr_equivalent = calculate_token_exchange(token_price_lum, token_price_smr, lum_amount, SMR_DECIMALS, LUM_DECIMALS)
        print(f"Swap {lum_amount} LUM into {smr_equivalent} SMR")

        # amount_in = truncate_to_upper_digits(web3.to_wei(lum_amount, 'ether'), LUM_DECIMALS-1)
        amount_in = web3.to_wei(lum_amount, 'ether')
        print(f"Amount IN: {amount_in} LUM")

        # Minimum amount of SMR you are willing to receive, set to 98% of calculated smr equivalent for simplicity
        amount_out_min = web3.to_wei(smr_equivalent * 0.98, 'mwei')
        print(f"Amount OUT MIN: {amount_out_min} glow")

        # Approve the LUM amount first
        amount_to_approve = web3.to_wei(lum_amount, 'ether')  # Amount of LUM to approve
        approve_receipt = approve_token(web3, my_account, private_key, TOKEN_ADDRESS_LUM, SHIMMERSEA_SWAP_SPENDER_ADDRESS, amount_to_approve, SHIMMER_CHAIN_ID,
                                        SHIMMER_GAS_UPPER_LIMIT,
                                        SHIMMER_GAS_PRICE)
        print(approve_receipt)
        status = check_transaction_status(approve_receipt)

        if status != 1:
            raise ValueError(f"Could not approve {lum_amount} LUM.")

        path = [TOKEN_ADDRESS_LUM, TOKEN_ADDRESS_SMR]  # Path for the swap
        to = my_account  # Address receiving the SMR
        deadline = int(time.time()) + 10 * 60  # Transaction deadline (10 minutes from now)

        # Swap the LUM for SMR
        txn_receipt = shimmersea_swap(web3, my_account, private_key, amount_in, amount_out_min, path, to, deadline, SHIMMER_CHAIN_ID, SHIMMER_GAS_UPPER_LIMIT,
                                      SHIMMER_GAS_PRICE)
        print(txn_receipt)
        status = check_transaction_status(txn_receipt)

    else:
        print("No option selected.")


if __name__ == "__main__":
    main()
