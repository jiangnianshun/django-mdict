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


class MdictEntrySerializer(serializers.Serializer):
    mdx_name = serializers.CharField(max_length=100)
    mdx_entry = serializers.CharField()
    mdx_record = serializers.CharField()
    mdx_pror = serializers.IntegerField()
    pk = serializers.IntegerField()
    extra = serializers.CharField()
