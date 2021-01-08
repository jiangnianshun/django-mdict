from rest_framework import serializers
from mdict.models import MyMdictEntry, MyMdictEntryType, MyMdictItem, MdictDic, MdictOnline


class MyMdictEntryTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyMdictEntryType
        fields = ('mdict_type',)


class MyMdictItemSerializer(serializers.ModelSerializer):
    item_type = MyMdictEntryTypeSerializer(read_only=True)

    class Meta:
        model = MyMdictItem
        fields = ('item_entry', 'item_type', 'item_content')


class MyMdictEntrySerializer(serializers.ModelSerializer):
    # mdict_group = MyMdictEntryGroupSerializer(read_only=True)
    mymdictitem_set = MyMdictItemSerializer(many=True, read_only=True)

    # mymdictitem_set是外键的反向查询，这里mymdictitem是模型MyMdictItem的小写，后加_set，或者在MyMdictItem指向MyMdictEntry的外键中添加related_name='mdict_name'，然后这里用mdict_name，如果不用上面两个方法，最后解析的json中没有这个字段。
    class Meta:
        model = MyMdictEntry
        fields = ('mdict_entry', 'mdict_group', 'mymdictitem_set')


class MdictDicSerializer(serializers.ModelSerializer):
    class Meta:
        model = MdictDic
        fields = ('mdict_name',)


class MdictOnlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = MdictOnline
        fields = ('mdict_name', 'mdict_url', 'mdict_enable', 'mdict_priority', 'mdict_isiframe')


class mdxentry():
    def __init__(self, m_name, m_entry, m_record, m_pror, pk, f_pk, p1, p2):
        self.mdx_name = m_name
        self.mdx_entry = m_entry
        self.mdx_record = m_record
        self.mdx_pror = m_pror
        self.pk = pk
        self.f_pk = f_pk  # f_pk,f_p1,f_p2是该词条最终指向（LINK）的词条所在词典的id，以及位置p1,p2
        self.f_p1 = p1
        self.f_p2 = p2


class MdictEntrySerializer(serializers.Serializer):
    mdx_name = serializers.CharField(max_length=100)
    mdx_entry = serializers.CharField()
    mdx_record = serializers.CharField()
    mdx_pror = serializers.IntegerField()
    pk = serializers.IntegerField()
