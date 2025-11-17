# uavledger/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import hashlib
from services.contract import (
    w3,
    get_chain_info,
    contract,
    send_txn,
)

# -----------------------------
# ETH STATUS ENDPOINT
# -----------------------------
def eth_status(request):
    info = get_chain_info()
    return JsonResponse(info)


# -----------------------------
# LOG MISSION → blockchain
# POST /api/missions/<mission_id>/log
# -----------------------------
@csrf_exempt
def log_mission(request, mission_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        body = json.loads(request.body.decode())
        s3_key = body.get("s3_key")

        if not s3_key:
            return JsonResponse({"error": "Missing s3_key"}, status=400)

        # Convert missionId → bytes32
        mission_hash = Web3.to_bytes(hexstr=mission_id) if mission_id.startswith("0x") \
                       else hashlib.sha256(mission_id.encode()).digest()

        # Build blockchain transaction
        tx_hash = send_txn(
            contract.functions.logFlight(mission_hash, s3_key)
        )

        return JsonResponse({
            "status": "submitted",
            "tx_hash": tx_hash,
            "mission_id": mission_id,
            "s3_key": s3_key,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# -----------------------------
# GET MISSION LOG → blockchain
# GET /api/missions/<mission_id>/log/details
# -----------------------------
def get_mission(request, mission_id):
    try:
        # Convert missionId → bytes32
        mission_hash = Web3.to_bytes(hexstr=mission_id) if mission_id.startswith("0x") \
                       else hashlib.sha256(mission_id.encode()).digest()

        s3_key, ts, uploader = contract.functions.getFlight(mission_hash).call()

        return JsonResponse({
            "mission_id": mission_id,
            "s3_key": s3_key,
            "timestamp": ts,
            "uploader": uploader,
            "exists": s3_key != "",
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
