from django.contrib import admin
import subprocess
from elasticsearch import Elasticsearch
from base.base_config import *
from base.base_sys import check_system
from .models import MdictDic, MdictOnline, MyMdictEntry, MyMdictItem, MyMdictEntryType, MdictDicGroup


def EnableAllDics(modeladmin, request, queryset):
    queryset.update(mdict_enable=True)


EnableAllDics.short_description = "启用选择的词典"


def DisableAllDics(modeladmin, request, queryset):
    queryset.update(mdict_enable=False)


DisableAllDics.short_description = "关闭选择的词典"


def EnableAllEs(modeladmin, request, queryset):
    queryset.update(mdict_es_enable=True)


EnableAllEs.short_description = "开启es索引"


def DisableAllEs(modeladmin, request, queryset):
    queryset.update(mdict_es_enable=False)


DisableAllEs.short_description = "禁止es索引"

script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'script')


def createAllIndex(modeladmin, request, queryset):
    try:
        cmd = ['mdict_es.py']
        if check_system() == 0:
            cmd.insert(0, 'python3')
        else:
            cmd.insert(0, 'python')

        all_dics = MdictDic.objects.all()
        if len(queryset) < len(all_dics):
            cmd.append('-c')
            for dic in queryset:
                cmd.append(str(dic.pk))
        else:
            cmd.append('-ca')

        command = ' '.join(cmd)
        # 直接传cmd，在ubuntu里可能不会正确运行脚本，而是打开了python解释器，需要转换为字符串。

        print('running script:', command)
        subprocess.Popen(command, shell=True, cwd=script_path)
    except Exception as e:
        print(e)


createAllIndex.short_description = "创建es索引"


def deleteAllIndex(modeladmin, request, queryset):
    try:
        es_host = get_config_con('es_host')
        client = Elasticsearch(hosts=es_host)
        indices = client.indices
        for dic in queryset:
            dic_md5 = dic.mdict_md5
            if dic_md5 != '' and dic_md5 is not None:
                index_name = 'mdict-' + dic_md5
                indices.delete(index=index_name, ignore=[400, 404])
                print('delete', dic.mdict_name, dic.mdict_file, dic.pk, index_name)
        print('delete operation has completed.')
    except Exception as e:
        print(e)


deleteAllIndex.short_description = "删除es索引"


class MdictDicAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'mdict_file', 'mdict_name', 'get_mdict_groups', 'mdict_enable', 'mdict_es_enable', 'mdict_priority')
    # list_display不能是manytomanyfield
    list_filter = ['mdictdicgroup', 'mdict_enable', 'mdict_es_enable']
    search_fields = ['mdict_name', 'mdict_file', 'id']
    list_display_links = ['mdict_file']
    actions = [EnableAllDics, DisableAllDics, EnableAllEs, DisableAllEs, createAllIndex, deleteAllIndex]
    # list_per_page = sys.maxsize  # 设置每页数目最大
    list_per_page = 30
    ordering = ('mdict_priority',)  # 按照mdict_priority的降序排列
    # filter_horizontal = ('mdict_group',)
    list_editable = ['mdict_priority', 'mdict_enable', 'mdict_name', 'mdict_es_enable']

    # 默认的MangToMany的样式是在一个方框内按住ctrl键选择多个对象，filter_horizontal设置水平两个方框，将对象左右移动。

    @staticmethod
    def get_mdict_groups(obj):
        return "|".join([g.dic_group_name for g in obj.mdictdicgroup_set.all()])


class MyMdictItemAdmin(admin.StackedInline):
    model = MyMdictItem
    extra = 1


class MyMdictEntryAdmin(admin.ModelAdmin):
    inlines = [MyMdictItemAdmin]
    list_display = ('id', 'mdict_entry')
    search_fields = ['mdict_entry']
    list_editable = ['mdict_entry']


class MyMdictEntryTypeAdmin(admin.ModelAdmin):
    ordering = ('mdict_type',)


class MdictOnlineAdmin(admin.ModelAdmin):
    list_display = ('id', 'mdict_name', 'mdict_enable', 'mdict_priority', 'mdict_isiframe', 'mdict_url')
    list_editable = ('mdict_name', 'mdict_priority', 'mdict_enable', 'mdict_name')
    ordering = ('mdict_priority',)


class MdictDicGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'dic_group_name')
    list_editable = ('dic_group_name',)
    filter_horizontal = ('mdict_group',)


# Register your models here.

admin.site.register(MdictDic, MdictDicAdmin)
admin.site.register(MdictDicGroup, MdictDicGroupAdmin)
admin.site.register(MdictOnline, MdictOnlineAdmin)
admin.site.register(MyMdictEntry, MyMdictEntryAdmin)
admin.site.register(MyMdictEntryType, MyMdictEntryTypeAdmin)
