import json
import os

from django.http import HttpResponse
from django.shortcuts import render

from .models import Webgroup, Website
from .icon_utils import get_icons_set, get_icon


def mynav_index(request):
    user_login = False
    user_portrait = 'image/default.jpg'
    webgroup = Webgroup.objects.all().order_by('group_priority')

    context = {'webgroup': webgroup, 'user_login': user_login,
               'user_portrait': user_portrait}
    return render(request, 'mynav/mynav.html', context)


def add_site(request):
    site_name = request.GET.get('site_name')
    site_url = request.GET.get('site_url')
    site_group = int(request.GET.get('site_group', 0))
    site_priority = int(request.GET.get('site_priority', 1))
    site_brief = request.GET.get('site_brief', '')
    if site_group == 0:
        webgroup = None
    else:
        webgroup = Webgroup.objects.get(pk=site_group)

    site_obj = Website.objects.create(site_name=site_name, site_url=site_url, site_group=webgroup,
                                      site_priority=site_priority,
                                      site_brief=site_brief)

    if webgroup is None:
        group_name = '无分组'
    else:
        group_name = webgroup.group_name

    get_icon(site_url, site_obj.pk)

    return HttpResponse(json.dumps({
        'site_name': site_name,
        'site_url': site_url,
        'site_group': group_name,
        'site_brief': site_brief
    }))


def get_site(request):
    icons_set = get_icons_set()
    groups = Webgroup.objects.all().order_by('group_priority', 'group_name')
    groups_list = []
    for group in groups:
        sites = group.website_set.all().order_by('site_priority', 'site_name')
        sites_list = []
        for site in sites:
            if site.id in icons_set:
                site_icon = True
            else:
                site_icon = False
            sites_list.append((site.pk, site.site_name, site.site_url, site_icon, site.site_brief))
        group_item = (group.pk, group.group_name, sites_list)
        if len(sites_list) > 0:
            groups_list.append(group_item)

    extra_sites = Website.objects.filter(site_group=None)
    sites_list = []
    for site in extra_sites:
        sites_list.append((site.site_name, site.site_url))
    if len(sites_list) > 0:
        groups_list.append(('未分组', sites_list))
    return HttpResponse(json.dumps(groups_list))


def edit_site(request):
    cur_pk = int(request.GET.get('cur_pk', 0))
    prev_pk = int(request.GET.get('prev_pk', 0))
    group_pk = int(request.GET.get('group_pk', 0))
    if cur_pk > 0:
        cur_site = Website.objects.get(pk=cur_pk)
        if prev_pk > 0:
            prev_site = Website.objects.get(pk=prev_pk)
            site_priority = prev_site.site_priority + 1
        else:
            site_priority = 1
        if group_pk > 0:
            group_obj = Webgroup.objects.get(pk=group_pk)
            cur_site.site_priority = site_priority
            cur_site.site_group = group_obj
            cur_site.save()
        else:
            cur_site.site_priority = site_priority
            cur_site.save()

        return HttpResponse('success')
    return HttpResponse('error')


def add_group(request):
    group_name = request.GET.get('group_name')
    group_priority = int(request.GET.get('group_priority', 1))
    Webgroup.objects.create(group_name=group_name, group_priority=group_priority)
    return HttpResponse('success')


def get_group(request):
    groups = Webgroup.objects.all().order_by('group_priority')
    group_list = []
    for group in groups:
        group_list.append([group.pk, group.group_name])
    return HttpResponse(json.dumps(group_list))
