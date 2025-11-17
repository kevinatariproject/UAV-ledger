# services/eth_client.py

import os
from dotenv import load_dotenv
from web3 import Web3

# Load variables from .env into environment
load_dotenv()

# ==== Read values from .env ====
ETH_RPC_URL = os.getenv("ETH_RPC_URL")
CHAIN_ID = int(os.getenv("CHAIN_ID", "11155111"))  # default: Sepolia
ETH_PRIVATE_KEY = os.getenv("ETH_PRIVATE_KEY")
CONTRACT_ADDRESS_RAW = os.getenv("CONTRACT_ADDRESS")

if not ETH_RPC_URL:
    raise RuntimeError("ETH_RPC_URL is not set in .env")

if not ETH_PRIVATE_KEY:
    raise RuntimeError("ETH_PRIVATE_KEY is not set in .env")

if not CONTRACT_ADDRESS_RAW:
    raise RuntimeError("CONTRACT_ADDRESS is not set in .env")

# Create a Web3 object that talks to Sepolia via your Infura URL
w3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))

# Normalize contract address to checksum format
CONTRACT_ADDRESS = Web3.to_checksum_address(CONTRACT_ADDRESS_RAW)

# Derive the public address from the private key (this is your Sepolia wallet)
ACCOUNT = w3.eth.account.from_key(ETH_PRIVATE_KEY)
ACCOUNT_ADDRESS = ACCOUNT.address

# ===========================
# FlightLogRegistry ABI
# (copied from Remix, simplified to just what we need)
# ===========================
FLIGHT_LOG_REGISTRY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "missionId",
                "type": "bytes32",
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "s3Key",
                "type": "string",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "uploader",
                "type": "address",
            },
        ],
        "name": "FlightLogged",
        "type": "event",
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "",
                "type": "bytes32",
            }
        ],
        "name": "flightLogs",
        "outputs": [
            {
                "internalType": "string",
                "name": "s3Key",
                "type": "string",
            },
            {
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256",
            },
            {
                "internalType": "address",
                "name": "uploader",
                "type": "address",
            },
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "missionId",
                "type": "bytes32",
            }
        ],
        "name": "getFlight",
        "outputs": [
            {
                "internalType": "string",
                "name": "s3Key",
                "type": "string",
            },
            {
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256",
            },
            {
                "internalType": "address",
                "name": "uploader",
                "type": "address",
            },
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "missionId",
                "type": "bytes32",
            },
            {
                "internalType": "string",
                "name": "s3Key",
                "type": "string",
            },
        ],
        "name": "logFlight",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


def get_contract():
    """
    Build a Web3 contract object for FlightLogRegistry.
    """
    return w3.eth.contract(address=CONTRACT_ADDRESS, abi=FLIGHT_LOG_REGISTRY_ABI)


def mission_id_to_bytes32(mission_id: str) -> bytes:
    """
    Convert a human-readable mission_id string into bytes32.

    Here we use keccak hash so:
      - input: "mission-123"
      - result: 32-byte hash used as key in the contract.
    """
    return Web3.keccak(text=mission_id)


def get_chain_info():
    """
    Simple helper function that returns basic info
    about the chain we are connected to and the contract.
    """
    connected = w3.is_connected()
    node_chain_id = None
    latest_block = None

    if connected:
        node_chain_id = w3.eth.chain_id
        latest_block = w3.eth.block_number

    return {
        "connected": connected,
        "rpc_url": ETH_RPC_URL,
        "configured_chain_id": CHAIN_ID,
        "node_chain_id": node_chain_id,
        "latest_block": latest_block,
        "contract_address": CONTRACT_ADDRESS,
        "account_address": ACCOUNT_ADDRESS,
    }


def log_flight_on_chain(mission_id: str, s3_key: str):
    """
    Call logFlight(missionId, s3Key) on the smart contract.

    Steps:
      1. Convert mission_id string -> bytes32 key.
      2. Build transaction.
      3. Sign transaction with our private key.
      4. Send to Sepolia and wait for receipt.
    """
    if not w3.is_connected():
        raise RuntimeError("Not connected to Ethereum node")

    contract = get_contract()
    mission_key = mission_id_to_bytes32(mission_id)

    # Build the transaction
    nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)

    tx = contract.functions.logFlight(mission_key, s3_key).build_transaction(
        {
            "from": ACCOUNT_ADDRESS,
            "nonce": nonce,
            "chainId": CHAIN_ID,
            "gasPrice": w3.eth.gas_price,
        }
    )

    # Sign with our private key
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=ETH_PRIVATE_KEY)

    # Send and wait for receipt
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "mission_id": mission_id,
        "mission_key": mission_key.hex(),
        "s3_key": s3_key,
        "transaction_hash": tx_hash.hex(),
        "block_number": receipt.block_number,
        "status": receipt.status,
    }


def get_flight_from_chain(mission_id: str):
    """
    Call getFlight(missionId) on the smart contract.

    Returns:
      {
        "mission_id": "...",
        "mission_key": "0x...",
        "s3_key": "...",
        "timestamp": <int>,
        "uploader": "0x...",
        "exists": True/False
      }
    """
    if not w3.is_connected():
        raise RuntimeError("Not connected to Ethereum node")

    contract = get_contract()
    mission_key = mission_id_to_bytes32(mission_id)

    s3_key, timestamp, uploader = contract.functions.getFlight(mission_key).call()

    # If no log yet, s3_key will be empty string.
    exists = s3_key != ""

    return {
        "mission_id": mission_id,
        "mission_key": mission_key.hex(),
        "s3_key": s3_key,
        "timestamp": int(timestamp),
        "uploader": uploader,
        "exists": exists,
    }
