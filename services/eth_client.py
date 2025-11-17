import os
import json
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from web3 import Web3

# ================================
# 1) Load environment variables
# ================================
load_dotenv()

ETH_RPC_URL = os.getenv("ETH_RPC_URL")
CHAIN_ID = int(os.getenv("CHAIN_ID", "11155111"))  # Sepolia default
ETH_PRIVATE_KEY = os.getenv("ETH_PRIVATE_KEY")
CONTRACT_ADDRESS_RAW = os.getenv("CONTRACT_ADDRESS")

if not ETH_RPC_URL:
    raise RuntimeError("ETH_RPC_URL is not set in .env")

if not ETH_PRIVATE_KEY:
    raise RuntimeError("ETH_PRIVATE_KEY is not set in .env")

if not CONTRACT_ADDRESS_RAW:
    raise RuntimeError("CONTRACT_ADDRESS is not set in .env")

# ===================================
# 2) Connect to Sepolia via Web3
# ===================================
w3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))

# Normalize contract address to checksum format
CONTRACT_ADDRESS = Web3.to_checksum_address(CONTRACT_ADDRESS_RAW)

# Derive the public address from the private key
ACCOUNT = w3.eth.account.from_key(ETH_PRIVATE_KEY)
ACCOUNT_ADDRESS = ACCOUNT.address

# ===================================
# 3) Contract ABI (from your metadata)
#    We keep it as JSON string and parse it.
# ===================================
ABI_JSON = """
[
  {
    "name": "FlightLogged",
    "type": "event",
    "inputs": [
      {
        "name": "missionId",
        "type": "bytes32",
        "indexed": true,
        "internalType": "bytes32"
      },
      {
        "name": "s3Key",
        "type": "string",
        "indexed": false,
        "internalType": "string"
      },
      {
        "name": "timestamp",
        "type": "uint256",
        "indexed": false,
        "internalType": "uint256"
      },
      {
        "name": "uploader",
        "type": "address",
        "indexed": true,
        "internalType": "address"
      }
    ],
    "anonymous": false
  },
  {
    "name": "flightLogs",
    "type": "function",
    "inputs": [
      {
        "name": "",
        "type": "bytes32",
        "internalType": "bytes32"
      }
    ],
    "outputs": [
      {
        "name": "s3Key",
        "type": "string",
        "internalType": "string"
      },
      {
        "name": "timestamp",
        "type": "uint256",
        "internalType": "uint256"
      },
      {
        "name": "uploader",
        "type": "address",
        "internalType": "address"
      }
    ],
    "stateMutability": "view"
  },
  {
    "name": "getFlight",
    "type": "function",
    "inputs": [
      {
        "name": "missionId",
        "type": "bytes32",
        "internalType": "bytes32"
      }
    ],
    "outputs": [
      {
        "name": "s3Key",
        "type": "string",
        "internalType": "string"
      },
      {
        "name": "timestamp",
        "type": "uint256",
        "internalType": "uint256"
      },
      {
        "name": "uploader",
        "type": "address",
        "internalType": "address"
      }
    ],
    "stateMutability": "view"
  },
  {
    "name": "logFlight",
    "type": "function",
    "inputs": [
      {
        "name": "missionId",
        "type": "bytes32",
        "internalType": "bytes32"
      },
      {
        "name": "s3Key",
        "type": "string",
        "internalType": "string"
      }
    ],
    "outputs": [],
    "stateMutability": "nonpayable"
  }
]
"""

CONTRACT_ABI = json.loads(ABI_JSON)

# Create a contract object
contract = w3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=CONTRACT_ABI,
)

# ===================================
# 4) Helper: basic chain info (already used)
# ===================================
def get_chain_info() -> Dict[str, Any]:
    """
    Return basic info about the chain we are connected to
    and the contract/account we use.
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

# ===================================
# 5) Internal helper: missionId → bytes32
# ===================================
def _mission_id_to_bytes32(mission_id: str) -> bytes:
    """
    Convert a human-readable mission ID string into a bytes32 value.

    We use keccak(text=mission_id) so the same mission_id string
    always maps to the same bytes32.
    """
    return Web3.keccak(text=mission_id)


# ===================================
# 6) Write: logFlight on-chain
# ===================================
def log_flight_on_chain(mission_id: str, s3_key: str) -> str:
    """
    Store or update a flight log on-chain.

    - mission_id: a human-readable ID like 'mission-123'
    - s3_key: the S3 object key where the log is stored

    Returns: transaction hash (hex string)
    """
    if not w3.is_connected():
        raise RuntimeError("Not connected to Ethereum node")

    mission_bytes = _mission_id_to_bytes32(mission_id)

    # Build the transaction
    nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)
    gas_price = w3.eth.gas_price  # simple legacy-style gas

    tx = contract.functions.logFlight(mission_bytes, s3_key).build_transaction(
        {
            "from": ACCOUNT_ADDRESS,
            "nonce": nonce,
            "gas": 200000,        # rough gas limit
            "gasPrice": gas_price,
            "chainId": CHAIN_ID,
        }
    )

    # Sign and send
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=ETH_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Return hex string so we can show it in the UI / logs
    return tx_hash.hex()


# ===================================
# 7) Read: getFlight from chain
# ===================================
def get_flight_from_chain(mission_id: str) -> Optional[Dict[str, Any]]:
    """
    Read a flight log from the chain.

    Returns:
      {
        "s3_key": str,
        "timestamp": int,
        "uploader": str
      }
    or None if nothing found.
    """
    if not w3.is_connected():
        raise RuntimeError("Not connected to Ethereum node")

    mission_bytes = _mission_id_to_bytes32(mission_id)

    s3_key, timestamp, uploader = contract.functions.getFlight(mission_bytes).call()

    # If no log is stored, s3_key will likely be an empty string.
    if s3_key == "":
        return None

    return {
        "s3_key": s3_key,
        "timestamp": int(timestamp),
        "uploader": uploader,
    }
