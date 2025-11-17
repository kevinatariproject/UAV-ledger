from django.http import JsonResponse

from services.eth_client import get_chain_info


def chain_info_view(request):
    """
    Simple API endpoint to show:
    - if we're connected to Sepolia
    - what chain id the node reports
    - latest block number
    """
    data = get_chain_info()
    return JsonResponse(data)
