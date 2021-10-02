from django.urls import path
from . import views

app_name = 'mynav'
urlpatterns = [
    path('', views.mynav_index, name='mynav'),
    path('addsite/', views.add_site, name='addsite'),
    path('getsite/', views.get_site, name='getsite'),
    path('addgroup/', views.add_group, name='addgroup'),
    path('getgroup/', views.get_group, name='getgroup'),
]