from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from base.base_constant import regp


class MdictOnline(models.Model):
    mdict_name = models.CharField('词典名', max_length=20)
    mdict_url = models.URLField('网址')
    mdict_enable = models.BooleanField('启用', default=False)
    mdict_priority = models.PositiveIntegerField('词典排序', default=1)  # 优先级显示，validator设置范围
    mdict_isiframe = models.BooleanField('在iframe中打开', default=True)

    class Meta:
        verbose_name = '在线词典'
        verbose_name_plural = '在线词典'

    def __str__(self):
        return self.mdict_name

    def save(self, *args, **kwargs):
        mdict_order(self, MdictOnline)

        super(MdictOnline, self).save()


class MdictDic(models.Model):
    mdict_name = models.CharField('词典名', max_length=100, unique=True)
    mdict_file = models.CharField('文件名', max_length=100, unique=True)
    mdict_enable = models.BooleanField('启用', default=True)
    mdict_priority = models.PositiveIntegerField('词典排序', default=1)  # 优先级显示，validator设置范围
    # mdict_group = models.ManyToManyField('MdictDicGroup', verbose_name='词典分组', blank=True)

    class Meta:
        verbose_name = 'Mdict词典'
        verbose_name_plural = 'Mdict词典'

    def __str__(self):
        return self.mdict_name

    def save(self, *args, **kwargs):
        mdict_order(self, MdictDic)

        super(MdictDic, self).save()


def mdict_order(obj, mdl):
    if obj.mdict_priority == 0:
        obj.mdict_priority = 1

    mdict_dic = mdl.objects.all().order_by('mdict_priority')

    mdict_dic_len = len(mdict_dic)

    if obj.mdict_priority > mdict_dic_len:
        obj.mdict_priority = mdict_dic_len

    for i in range(mdict_dic_len):
        if i + 1 != mdict_dic[i].mdict_priority:
            mdict_dic.filter(pk=mdict_dic[i].pk).update(mdict_priority=i + 1)

    mdict_dic = mdl.objects.all().order_by('mdict_priority')
    w1 = mdict_dic.filter(pk=obj.pk)
    if len(w1) > 0:  # 新添加的词典还不存在
        real_order = w1[0].mdict_priority

        if obj.mdict_priority > real_order:  # 向后移动，后面的都向前补一位
            w2 = mdict_dic.filter(mdict_priority__gt=real_order, mdict_priority__lte=obj.mdict_priority)
            for w in w2:
                w2.filter(mdict_priority=w.mdict_priority).update(mdict_priority=w.mdict_priority - 1)

        elif obj.mdict_priority < real_order:
            w2 = mdict_dic.filter(mdict_priority__lt=real_order, mdict_priority__gte=obj.mdict_priority).order_by(
                '-mdict_priority')
            for w in w2:
                w2.filter(mdict_priority=w.mdict_priority).update(mdict_priority=w.mdict_priority + 1)


class MdictDicGroup(models.Model):
    dic_group_name = models.CharField('分组名', max_length=100, unique=True)
    mdict_group = models.ManyToManyField('MdictDic', verbose_name='词典', blank=True)

    class Meta:
        verbose_name = '词典分组'
        verbose_name_plural = '词典分组'

    def __str__(self):
        return self.dic_group_name


class MyMdictEntryType(models.Model):
    mdict_type = models.CharField('标签', max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'

    def __str__(self):
        return self.mdict_type


class MyMdictEntry(models.Model):
    mdict_entry = models.CharField('词条', max_length=100, db_index=True, unique=True)
    mdict_entry_strip = models.CharField('STRIP词条', max_length=100, blank=True, null=True, editable=False)

    class Meta:
        verbose_name = '内置词条'
        verbose_name_plural = '内置词条'

    def __str__(self):
        return self.mdict_entry

    def save(self, *args, **kwargs):
        self.mdict_entry = self.mdict_entry.strip()
        self.mdict_entry_strip = regp.sub('', self.mdict_entry)
        super(MyMdictEntry, self).save()


ckeditor_ext_plugins = [
    ('mlink', '/static/mdict/ckeditor/plugins/mlink/', 'plugin.js',),
    ('mwrap', '/static/mdict/ckeditor/plugins/mwrap/', 'plugin.js',),
    ('mathjax', '/static/mdict/ckeditor/plugins/mathjax/', 'plugin.js',),
]


class MyMdictItem(models.Model):
    item_mdict = models.ForeignKey('MyMdictEntry', verbose_name='词条', null=True, blank=True, on_delete=models.SET_NULL)
    item_entry = models.CharField('义项', max_length=100, blank=True, null=True)
    item_entry_strip = models.CharField('STRIP义项', max_length=100, blank=True, null=True, editable=False)
    item_type = models.ForeignKey('MyMdictEntryType', verbose_name='义项类别', null=True, blank=True,
                                  on_delete=models.SET_NULL)
    item_content = RichTextUploadingField('义项内容', null=True, blank=True,
                                          external_plugin_resources=ckeditor_ext_plugins, )

    # RichTextField只能插入网络图片，如果要本地上传图片，需要用RichTextUploadingField

    class Meta:
        verbose_name = '义项'
        verbose_name_plural = '义项'

    def save(self, *args, **kwargs):
        if self.item_entry is not None:
            self.item_entry = self.item_entry.strip()
            self.item_entry_strip = regp.sub('', self.item_entry)
        super(MyMdictItem, self).save()
