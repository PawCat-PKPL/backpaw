from rest_framework.response import Response

def api_response(status_code, message, data=None):
    if data is None:
        data = []
    return Response({
        "status": status_code,
        "message": message,
        "data": data
    }, status=status_code)
