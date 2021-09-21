from django.db import models
from base.base_func import item_order


class Webgroup(models.Model):
    group_name = models.CharField('分组', max_length=15, unique=True)
    group_priority = models.PositiveIntegerField('分组排序', default=1)

    class Meta:
        verbose_name = '分组'
        verbose_name_plural = '分组'
        # 修改显示在admin界面上的模块名

    def save(self, *args, **kwargs):
        item_order(self, Webgroup, 'group')

        super(Webgroup, self).save()

    def __str__(self):
        return self.group_name


class Website(models.Model):
    site_name = models.CharField('名称', max_length=25)
    site_url = models.URLField('网址', unique=True)
    site_group = models.ForeignKey(Webgroup, verbose_name='分组', on_delete=models.SET_NULL, null=True, blank=True)
    # 将外键指向group_name会导致修改group_name时报错FOREIGN KEY constraint failed。
    site_brief = models.TextField('备注', blank=True)
    site_priority = models.PositiveIntegerField('网站排序', default=1)

    class Meta:
        verbose_name = '网站'
        verbose_name_plural = '网站'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # if not (self.site_url.lower().startswith('http://') or self.site_url.lower().startswith(
        #         'https://') or self.site_url.lower().startswith('chrome://')):
        #     self.site_url = 'http://' + self.site_url
        item_order(self, Website, 'site')
        super(Website, self).save()
