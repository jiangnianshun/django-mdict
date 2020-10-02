from django.contrib import admin

from .models import MdictDic, MdictOnline, MyMdictEntry, MyMdictItem, MyMdictEntryType, MdictDicGroup


def EnableAllDics(modeladmin, request, queryset):
    queryset.update(mdict_enable=True)
    EnableAllDics.short_description = "启用选择的词典"


def DisableAllDics(modeladmin, request, queryset):
    queryset.update(mdict_enable=False)
    DisableAllDics.short_description = "关闭选择的词典"


class MdictDicAdmin(admin.ModelAdmin):
    list_display = ('id', 'mdict_file', 'mdict_name', 'mdict_enable', 'mdict_priority')
    # list_display不能是manytomanyfield
    list_filter = ['mdict_priority']
    search_fields = ['mdict_name', 'mdict_file']
    list_display_links = ['mdict_file']
    actions = [EnableAllDics, DisableAllDics]
    # list_per_page = sys.maxsize  # 设置每页数目最大
    list_per_page = 30
    ordering = ('mdict_priority',)  # 按照mdict_priority的降序排列
    filter_horizontal = ('mdict_group',)
    list_editable = ['mdict_priority', 'mdict_enable', 'mdict_name']
    # 默认的MangToMany的样式是在一个方框内按住ctrl键选择多个对象，filter_horizontal设置水平两个方框，将对象左右移动。


class MyMdictItemAdmin(admin.TabularInline):
    model = MyMdictItem
    extra = 1


class MyMdictEntryAdmin(admin.ModelAdmin):
    inlines = [MyMdictItemAdmin]
    list_display = ('id', 'mdict_entry')
    # list_filter = ['mdict_group']
    search_fields = ['mdict_entry']


class MdictOnlineAdmin(admin.ModelAdmin):
    list_display = ('id', 'mdict_name', 'mdict_url', 'mdict_enable', 'mdict_isiframe')


# Register your models here.

admin.site.register(MdictDic, MdictDicAdmin)
admin.site.register(MdictDicGroup)
admin.site.register(MdictOnline, MdictOnlineAdmin)
admin.site.register(MyMdictEntry, MyMdictEntryAdmin)
admin.site.register(MyMdictEntryType)
