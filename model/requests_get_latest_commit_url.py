from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from .sfepy_pb_description.linear_elastic import *
from .sfepy_pb_description.connectToSpeckle import get_client, get_latest_commit_for_branch

@csrf_exempt
def get_latest_commit_url(request):
    if request.is_ajax and request.method == "POST":
        HOST = request.POST.get('HOST')
        STREAM_ID = request.POST.get('STREAM_ID')
        BRANCH = request.POST.get('BRANCH')

        print('HOST URL', HOST, STREAM_ID)
        
        
        client = get_client(HOST=HOST)
        main_latest_commit = get_latest_commit_for_branch(client, STREAM_ID, BRANCH)
        results_latest_commit = get_latest_commit_for_branch(client, STREAM_ID, 'results')

        # example url: `https://staging.speckle.dev/streams/a75ab4f10f/objects/f33645dc9a702de8af0af16bd5f655b0`
        main_url = f'{HOST}/streams/{STREAM_ID}/objects/{main_latest_commit.referencedObject}'
        if hasattr(results_latest_commit, 'referencedObject'):
            results_url = f'{HOST}/streams/{STREAM_ID}/objects/{results_latest_commit.referencedObject}'
        else:
            results_url = ''

        print('URL', main_url, results_url)

        return JsonResponse({'main_url': main_url, 'results_url': results_url}, status = 200)
    return JsonResponse({}, status = 400)