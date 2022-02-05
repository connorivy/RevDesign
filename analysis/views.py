from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def vue_test(request):
    return render(request, 'analysis/base.html')

# Create your views here.
def home(request):
    return render(request, 'analysis/base.html')