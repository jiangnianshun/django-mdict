from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'mdict'
urlpatterns = [
    path('', views.mdict_index),
    path('sug/', views.search_suggestion),
    url('(\d+)/(.+)', views.search_mdd),
    path('dic/', views.mdict_dic),
    url('dic/(\d+)/(.+)', views.search_mdd),
    path('audio/', views.search_audio),
    path('key/', views.search_mdx_key),
    path('record/', views.search_mdx_record),
    path('allentrys/', views.mdict_all_entrys),
    path('mdictlist/', views.get_mdict_list),
    path('header/', views.get_dic_info),
    path('dicgroup/', views.get_dic_group),
    path('exfile/', views.get_external_file),
    url('exfile/(.+)', views.get_external_file),
    path('mdictenable/', views.set_mdict_enable),
    path('retrieveconfig/', views.retrieve_config),
    path('saveconfig/', views.save_config),
    path('bujian/', views.bujianjiansuo),
]
