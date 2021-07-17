from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return HttpResponse('<h1>Analysis Home<h1>')

def beam(request):
    return HttpResponse('<h1>Analysis Beam<h1>')