import json
from web3 import Web3
import os
from django.conf import settings

# Load ABI
ABI_PATH = os.path.join(os.path.dirname(__file__), "contract_abi.json")
with open(ABI_PATH, "r") as f:
    ABI = json.load(f)

# Solidity contract bytecode (from your teammate)
BYTECODE = "PASTE_YOUR_CONTRACT_BYTECODE_HERE"

def deploy_contract():
    web3 = Web3(Web3.HTTPProvider(settings.ETH_RPC_URL))
    private_key = settings.ETH_PRIVATE_KEY
    account = web3.eth.account.from_key(private_key)
    address = account.address

    contract = web3.eth.contract(abi=ABI, bytecode=BYTECODE)

    # Build transaction
    tx = contract.constructor().build_transaction({
        "from": address,
        "nonce": web3.eth.get_transaction_count(address),
        "chainId": settings.CHAIN_ID,
        "gas": 500000,
        "gasPrice": web3.eth.gas_price
    })

    # Sign
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    print("Deploying contract... tx hash:")
    print(web3.to_hex(tx_hash))

    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print("Contract deployed at:")
    print(receipt.contractAddress)

    return receipt.contractAddress

if __name__ == "__main__":
    deploy_contract()
