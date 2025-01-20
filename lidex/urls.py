"""
URL configuration for lidex_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, re_path
from views import globmap, punti, raster_sample, raster_profilo, raster_clip,output_file,viewshed

urlpatterns = [
    path('lidex/map/', globmap),
    path('lidex/punti/', punti),
    re_path('^lidex/raster/$', raster_sample, name="raster_sample"),
    re_path('^lidex/profilo/(dtm|dsm)/$', raster_profilo, name="raster_profilo"),
    re_path('^lidex/output_file/(.*)/(.*)$', output_file, name="output_file"),
    re_path('^lidex/viewshed/$', viewshed, name="output_file"),
    re_path('^lidex/clip/$', raster_clip, name="raster_clip"),
]
