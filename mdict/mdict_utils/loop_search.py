from .decorator import loop_mdict_list, inner_object
from .search_object import SearchObject


@loop_mdict_list()
class loop_search_mdx_object(inner_object):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if dic.mdict_enable:  # 词典启用的情况下才会查询
            entry_list = []
            if self.group == 0:  # 默认查询全部词典
                entry_list = SearchObject(mdx, mdd_list, dic, self.query, g_id=g_id).search_mdx_entry()

            elif self.group == -1:
                if dic.mdict_priority <= 15:  # 词典排序
                    entry_list = SearchObject(mdx, mdd_list, dic, self.query, g_id=g_id).search_mdx_entry()
            else:  # 查询某个词典分组下的词典
                for pk, name in dic.mdict_group.values_list():
                    if pk == self.group:
                        entry_list = SearchObject(mdx, mdd_list, dic, self.query, g_id=g_id).search_mdx_entry()
                        break
            self.inner_list.extend(entry_list)


def loop_search_mdx(record_list, query, group):
    return loop_search_mdx_object({'query': query, 'inner_list': record_list, 'group': group})


@loop_mdict_list()
class loop_search_sug_object(inner_object):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if self.target_pk != -1:  # 只查询一个词典
            if dic.pk == self.target_pk:
                self.inner_list.extend(SearchObject(mdx, mdd_list, dic, self.query).search_sug_entry(self.flag))
                self.break_tag = True
        else:  # 全部查询
            if dic.mdict_enable:
                if self.group == 0:
                    self.inner_list.extend(SearchObject(mdx, mdd_list, dic, self.query).search_sug_entry(3))
                elif self.group == -1:
                    if dic.mdict_priority <= 15:
                        self.inner_list.extend(SearchObject(mdx, mdd_list, dic, self.query).search_sug_entry(3))
                else:  # 查询某个词典分组下的词典
                    for pk, name in dic.mdict_group.values_list():
                        if pk == self.group:
                            self.inner_list.extend(SearchObject(mdx, mdd_list, dic, self.query).search_sug_entry(3))
                            break


def loop_search_sug(target_pk, query, flag, group):
    return loop_search_sug_object({'query': query, 'target_pk': target_pk, 'flag': flag, 'group': group})
