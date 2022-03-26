from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from .sfepy_pb_description.linear_elastic import *
from .sfepy_pb_description.connectToSpeckle import get_client, get_latest_commit

@csrf_exempt
def get_latest_commit_url(request):
    if request.is_ajax and request.method == "POST":
        HOST = request.POST.get('HOST')
        STREAM_ID = request.POST.get('STREAM_ID')

        print('HOST URL', HOST, STREAM_ID)
        
        
        client = get_client(HOST=HOST)
        latest_commit = get_latest_commit(client, STREAM_ID)

        # example url: `https://staging.speckle.dev/streams/a75ab4f10f/objects/f33645dc9a702de8af0af16bd5f655b0`
        url = f'{HOST}/streams/{STREAM_ID}/objects/{latest_commit.referencedObject}'

        print('URL', url)

        return JsonResponse({'url': url}, status = 200)
    return JsonResponse({}, status = 400)