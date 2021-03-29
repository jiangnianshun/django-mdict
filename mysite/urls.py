from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.conf.urls import url
from django.shortcuts import render
from django.views.static import serve
from django.contrib.auth.models import User, Group
from django.http import HttpResponse

from mysite.settings import MEDIA_ROOT

from rest_framework import routers
from rest_framework import generics, permissions, serializers

from mdict import views as views_mdict

admin.autodiscover()


# first we define the serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', "first_name", "last_name")


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("name",)


# Create the API views
class UserList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetails(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    required_scopes = ['groups']
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


router = routers.DefaultRouter()
router.register(r'mdict2', views_mdict.MdictEntryViewSet, basename='mdict')
router.register(r'mymdict', views_mdict.MyMdictEntryViewSet)
router.register(r'mdictonline', views_mdict.MdictOnlineViewSet)


def redirect_font(request):  # url重定向
    return redirect('/media/font')


def main(request):
    return render(request, 'index.html')


def swView(request):
    with open(settings.BASE_DIR + "/static/js/sw.js") as fp:
        return HttpResponse(fp.read(), 'text/javascript')


urlpatterns = [
    path('', main, name='main'),
    path('api/', include(router.urls)),  # djangoresrframework生成的url
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('font/', redirect_font),
    path('mdict/', include('mdict.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^media/(?P<path>.*)$', serve, {"document_root": MEDIA_ROOT}),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),  # ckeditor的图片上传
    path('users/', UserList.as_view()),
    path('users/<pk>/', UserDetails.as_view()),
    path('groups/', GroupList.as_view()),
    path('sw.js', swView)
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
