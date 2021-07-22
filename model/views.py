from django.shortcuts import render
from django.http import HttpResponse
from .models import Member

# Create your views here.
def home(request):
    context = {
        'members': Member.objects.all()
    }
    return render(request, 'model/model.html', context) 