from .loop_decorator import loop_mdict_list, innerObject
from .search_object import SearchObject
from .mdict_func import get_dic_attrs
from mdict.models import MdictDicGroup


@loop_mdict_list()
class loop_search_mdx_object(innerObject):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if dic.mdict_enable:  # 词典启用的情况下才会查询
            entry_list = []
            if self.group == 0:  # 默认查询全部词典
                entry_list = SearchObject(mdx, mdd_list, get_dic_attrs(dic), self.query, g_id=g_id).search_entry()

            elif self.group == -1:
                if dic.mdict_priority <= 15:  # 词典排序
                    entry_list = SearchObject(mdx, mdd_list, get_dic_attrs(dic), self.query, g_id=g_id).search_entry()
            else:  # 查询某个词典分组下的词典
                group_list = MdictDicGroup.objects.filter(pk=self.group)
                if len(group_list) > 0:
                    temp = group_list[0].mdict_group.filter(pk=dic.pk)
                    if len(temp) > 0:
                        entry_list = SearchObject(mdx, mdd_list, get_dic_attrs(dic), self.query, g_id=g_id).search_entry()
            self.inner_list.extend(entry_list)


def loop_search_mdx(record_list, query, group):
    return loop_search_mdx_object({'query': query, 'inner_list': record_list, 'group': group})


@loop_mdict_list()
class loop_search_sug_object(innerObject):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if self.target_pk != -1:  # 只查询一个词典
            if dic.pk == self.target_pk:
                self.inner_list.extend(SearchObject(mdx, mdd_list, get_dic_attrs(dic), self.query).search_sug(self.flag))
                self.break_tag = True
        else:  # 全部查询
            if dic.mdict_enable:
                if self.group == 0:
                    self.inner_list.extend(SearchObject(mdx, mdd_list, get_dic_attrs(dic), self.query).search_sug(3))
                elif self.group == -1:
                    if dic.mdict_priority <= 15:
                        self.inner_list.extend(SearchObject(mdx, mdd_list, get_dic_attrs(dic), self.query).search_sug(3))
                else:  # 查询某个词典分组下的词典
                    group_list = MdictDicGroup.objects.filter(pk=self.group)
                    if len(group_list) > 0:
                        temp = group_list[0].mdict_group.filter(pk=dic.pk)
                        if len(temp) > 0:
                            self.inner_list.extend(SearchObject(mdx, mdd_list, get_dic_attrs(dic), self.query).search_sug(3))


def loop_search_sug(target_pk, query, flag, group):
    return loop_search_sug_object({'query': query, 'target_pk': target_pk, 'flag': flag, 'group': group})
