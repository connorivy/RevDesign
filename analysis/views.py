from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return render(request, 'analysis/home.html') 

def beam(request):
    return HttpResponse('<h1>Analysis Beam<h1>')

def report(request):
    return render(request, 'analysis/Report_Template.html')