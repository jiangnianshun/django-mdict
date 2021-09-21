from django.contrib import admin
from .models import Webgroup, Website


# Register your models here.

class WebsiteAdmin(admin.ModelAdmin):
    list_per_page = 50
    empty_value_display = '-empty-'
    list_display = ('pk', 'site_name', 'site_priority', 'site_group', 'site_url', 'site_brief')
    list_filter = ('site_group',)
    search_fields = ('site_name', 'site_url', 'site_brief')
    list_editable = ('site_name', 'site_priority', 'site_group')


class WebgroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'group_name', 'group_priority')
    ordering = ('group_priority',)
    list_editable = ('group_name', 'group_priority')


admin.site.register(Webgroup, WebgroupAdmin)
admin.site.register(Website, WebsiteAdmin)
admin.site.site_header = '管理员'
# site_header是admin界面最上面的标题，原内容为Django 管理。
admin.site.site_title = '管理'
# site_title是admin页面标签的内容，原内容为Django 站点管理员。