"""revdesign URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from analysis import views as analysis_views

from model import requests as model_requests

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', user_views.register, name='register'),
    path('analysis/', analysis_views.vue_test, name='analysis-vue_test'),
    path('', include('model.urls')),

    # AJAX requests
    path('post/ajax/validate/build_shearwalls', model_requests.build_shearwalls, name = "build_shearwalls"),
    path('post/ajax/validate/get_floor_mesh', model_requests.get_floor_mesh, name = "get_floor_mesh"),
    path('post/ajax/validate/analyze_mesh', model_requests.analyze_mesh, name = "analyze_mesh"),
    path('post/ajax/validate/send_to_stream', model_requests.send_to_stream, name = "send_to_stream"),
    path('post/ajax/validate/get_latest_commit_url', model_requests.get_latest_commit_url, name = "get_latest_commit_url"),
]
