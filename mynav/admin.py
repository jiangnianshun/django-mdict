from django.contrib import admin
from mynav.models import Webgroup, Website
from django.utils.translation import gettext_lazy as _

# Register your models here.

class WebsiteAdmin(admin.ModelAdmin):
    list_per_page = 50
    empty_value_display = '-empty-'
    list_display = ('pk', 'site_name', 'site_priority', 'site_group', 'site_url', 'site_brief')
    list_filter = ('site_group',)
    search_fields = ('site_name', 'site_url', 'site_brief')
    list_editable = ('site_name', 'site_priority', 'site_group')


class WebgroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'group_name', 'group_priority', 'get_website_num')
    ordering = ('group_priority',)
    list_editable = ('group_name', 'group_priority')

    @staticmethod
    def get_website_num(obj):
        return obj.website_set.all().count()


admin.site.register(Webgroup, WebgroupAdmin)
admin.site.register(Website, WebsiteAdmin)
admin.site.site_header = _('Administrator')
# site_header是admin界面最上面的标题，原内容为Django 管理。
admin.site.site_title = _('Administration')
# site_title是admin页面标签的内容，原内容为Django 站点管理员。