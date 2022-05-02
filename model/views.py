from django.shortcuts import render
from django.http import HttpResponse
from .models import *

# Create your views here.
def home(request):
    context = {
        'members': Member.objects.all(),
        # 'nodes': node.objects.all(),
        # 'local_members': define_local_members()
    }
    return render(request, 'model/sendToStream.html', context) 