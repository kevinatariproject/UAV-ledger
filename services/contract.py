import os
import json
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

# Load environment variables
ETH_RPC_URL = os.getenv("ETH_RPC_URL")
ETH_PRIVATE_KEY = os.getenv("ETH_PRIVATE_KEY")
CONTRACT_ADDRESS_RAW = os.getenv("CONTRACT_ADDRESS")
CHAIN_ID = int(os.getenv("CHAIN_ID", "11155111"))

if not ETH_RPC_URL:
    raise RuntimeError("ETH_RPC_URL must be set in .env")

if not ETH_PRIVATE_KEY:
    raise RuntimeError("ETH_PRIVATE_KEY must be set in .env")

if not CONTRACT_ADDRESS_RAW:
    raise RuntimeError("CONTRACT_ADDRESS must be set in .env")

# Connect Web3
w3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))

# Normalize contract address
CONTRACT_ADDRESS = Web3.to_checksum_address(CONTRACT_ADDRESS_RAW)

# Load ABI from file
ABI_PATH = os.path.join(os.path.dirname(__file__), "FlightLogRegistry_abi.json")

if not os.path.exists(ABI_PATH):
    raise RuntimeError(f"ABI file missing: {ABI_PATH}")

with open(ABI_PATH, "r") as f:
    CONTRACT_ABI = json.load(f)

# Create contract instance
contract = w3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=CONTRACT_ABI
)

# Derive account from private key
ACCOUNT = w3.eth.account.from_key(ETH_PRIVATE_KEY)
ACCOUNT_ADDRESS = ACCOUNT.address


def get_chain_info():
    """Return Web3 & contract health information."""
    return {
        "connected": w3.is_connected(),
        "rpc_url": ETH_RPC_URL,
        "configured_chain_id": CHAIN_ID,
        "node_chain_id": w3.eth.chain_id if w3.is_connected() else None,
        "latest_block": w3.eth.block_number if w3.is_connected() else None,
        "contract_address": CONTRACT_ADDRESS,
        "account_address": ACCOUNT_ADDRESS,
    }


def send_txn(fn):
    """
    Helper to sign + send contract transactions.
    `fn` is the contract function call, already built with parameters.
    """
    nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)

    txn = fn.build_transaction({
        "from": ACCOUNT_ADDRESS,
        "nonce": nonce,
        "chainId": CHAIN_ID,
        "gas": 500000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = w3.eth.account.sign_transaction(txn, ETH_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    return tx_hash.hex()
