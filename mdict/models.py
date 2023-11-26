from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from base.base_constant import regp
from base.base_utils import item_order
from django.utils.translation import gettext_lazy as _


class MdictOnline(models.Model):
    mdict_name = models.CharField(_('Dictionary Name'), max_length=20)
    mdict_url = models.URLField(_('URL'))
    mdict_enable = models.BooleanField(_('Enable'), default=False)
    mdict_priority = models.PositiveIntegerField(_('Priority'), default=1)  # 优先级显示，validator设置范围
    mdict_isiframe = models.BooleanField(_('open in iframe'), default=True)

    class Meta:
        verbose_name = _('Online Dictionary')
        verbose_name_plural = _('Online Dictionaries')

    def __str__(self):
        return self.mdict_name

    def save(self, *args, **kwargs):
        item_order(self, MdictOnline, 'mdict')

        super(MdictOnline, self).save()


class MdictDic(models.Model):
    mdict_name = models.CharField(_('Dictionary Name'), max_length=150, db_index=True)
    mdict_file = models.CharField(_('File Name'), max_length=150, db_index=True)
    # mdict_file设置unique=True会导致UNIQUE constraint failed
    mdict_enable = models.BooleanField(_('Enable'), default=True)
    mdict_priority = models.PositiveIntegerField(_('Priority'), default=1)  # 优先级显示，validator设置范围
    mdict_es_enable = models.BooleanField(_('Enable es index'), default=True, null=True)
    mdict_md5 = models.CharField(_('MD5'), max_length=35, default='', null=True, blank=True)

    class Meta:
        verbose_name = _('Local Dictionary')
        verbose_name_plural = _('Local Dictionaries')

    def __str__(self):
        return self.mdict_name

    def save(self, *args, **kwargs):
        try:
            item_order(self, MdictDic, 'mdict')
        except Exception as e:
            print(e)

        super(MdictDic, self).save()


class MdictDicGroup(models.Model):
    dic_group_name = models.CharField(_('Group Name'), max_length=100, unique=True)
    mdict_group = models.ManyToManyField('MdictDic', verbose_name=_('Dictionaries in Group'), blank=True)

    class Meta:
        verbose_name = _('Dictionary Group')
        verbose_name_plural = _('Dictionary Groups')

    def __str__(self):
        return self.dic_group_name


class MyMdictEntryType(models.Model):
    mdict_type = models.CharField(_('Label Name'), max_length=100, blank=True, null=True, unique=True)

    class Meta:
        verbose_name = _('Label')
        verbose_name_plural = _('Labels')

    def __str__(self):
        return self.mdict_type


class MyMdictEntry(models.Model):
    mdict_entry = models.CharField(_('Entry Name'), max_length=100, db_index=True, unique=True)
    mdict_entry_strip = models.CharField(_('Strip Entry'), max_length=100, blank=True, null=True, editable=False)

    class Meta:
        verbose_name = _('Built-in Entry')
        verbose_name_plural = _('Built-in Entries')

    def __str__(self):
        return self.mdict_entry

    def save(self, *args, **kwargs):
        self.mdict_entry = self.mdict_entry.strip()
        self.mdict_entry_strip = regp.sub('', self.mdict_entry)
        super(MyMdictEntry, self).save()


ckeditor_ext_plugins = [
    ('mlink', '/static/mdict/ckeditor/plugins/mlink/', 'plugin.js',),
    ('mwrap', '/static/mdict/ckeditor/plugins/mwrap/', 'plugin.js',),
    ('mruby', '/static/mdict/ckeditor/plugins/mruby/', 'plugin.js',),
    ('mbox', '/static/mdict/ckeditor/plugins/mbox/', 'plugin.js',),
    ('mathjax', '/static/mdict/ckeditor/plugins/mathjax/', 'plugin.js',),
]


class MyMdictItem(models.Model):
    item_mdict = models.ForeignKey('MyMdictEntry', verbose_name=_('Entry'), null=True, blank=True, on_delete=models.SET_NULL)
    item_entry = models.CharField(_('Subentry'), max_length=100, blank=True, null=True)
    item_entry_strip = models.CharField(_('Strip Subentry'), max_length=100, blank=True, null=True, editable=False)
    item_type = models.ForeignKey('MyMdictEntryType', verbose_name=_('Subentry Type'), null=True, blank=True,
                                  on_delete=models.SET_NULL)
    item_content = RichTextUploadingField(_('Subentry Contents'), null=True, blank=True,
                                          external_plugin_resources=ckeditor_ext_plugins, )

    # RichTextField只能插入网络图片，如果要本地上传图片，需要用RichTextUploadingField

    class Meta:
        verbose_name = _('Subentry')
        verbose_name_plural = _('Subentries')

    def save(self, *args, **kwargs):
        if self.item_entry is not None:
            self.item_entry = self.item_entry.strip()
            self.item_entry_strip = regp.sub('', self.item_entry)
        super(MyMdictItem, self).save()
