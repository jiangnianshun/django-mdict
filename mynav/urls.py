from django.urls import path
from . import views

app_name = 'mynav'
urlpatterns = [
    path('', views.mynav_index, name='mynav'),
    path('addsite/', views.addsite, name='addsite'),
    path('getsite/', views.getsite, name='getsite'),
    path('addgroup/', views.addgroup, name='addgroup'),
    path('getgroup/', views.getgroup, name='getgroup'),
]