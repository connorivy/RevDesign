from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse

@csrf_exempt
def send_to_stream(request):
    if request.is_ajax and request.method == "POST":
        pass
