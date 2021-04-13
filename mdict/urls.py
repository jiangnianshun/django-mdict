from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'mdict'
urlpatterns = [
    path('', views.mdict_index),
    path('sug/', views.search_suggestion),
    url('(\d+)/(.+)', views.search_mdd),
    url('dic/(\d+)/(.+)', views.search_mdd),
    url('es/(\d+)/(.+)', views.search_mdd),
    path('exfile/', views.get_external_file),
    url('exfile/(.+)', views.get_external_file),
    path('es/exfile/', views.get_external_file),
    url('es/exfile/(.+)', views.get_external_file),
    path('dic/', views.mdict_dic),
    path('audio/', views.search_audio),
    path('key/', views.search_mdx_key),
    path('record/', views.search_mdx_record),
    path('allentrys/', views.mdict_all_entrys),
    path('mdictlist/', views.get_mdict_list),
    path('header/', views.get_dic_info),
    path('dicgroup/', views.get_dic_group),
    path('mdictenable/', views.set_mdict_enable),
    path('retrieveconfig/', views.retrieve_config),
    path('saveconfig/', views.save_config),
    path('bujian/', views.bujianjiansuo),
    path('es/', views.es_index),
    path('essearch/', views.es_search),
    path('initindex/', views.init_index),
    path('indexstatus/', views.get_index_status),
    path('downloadhistory/', views.download_history),
    path('wordcloud/', views.wordcloud),
    path('getwordlist/', views.getwordlist),
    path('esdic/', views.es_dic),
]
