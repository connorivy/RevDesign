from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='analysis-home'),
    path('beam', views.beam, name='analysis-beam'),
]