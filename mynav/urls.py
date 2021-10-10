from django.urls import path
from . import views

app_name = 'mynav'
urlpatterns = [
    path('', views.mynav_index),
    path('addsite/', views.add_site),
    path('getsite/', views.get_site),
    path('editsite/', views.edit_site),
    path('addgroup/', views.add_group),
    path('getgroup/', views.get_group),
]