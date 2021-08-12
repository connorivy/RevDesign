from django.shortcuts import render
from django.http import HttpResponse
from .models import Member
from utils.read_in_rev_model_txt_file import *

# Create your views here.
def home(request):
    context = {
        'members': Member.objects.all(),
        'local_members': define_local_members()
    }
    return render(request, 'model/model.html', context) 