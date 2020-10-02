from .data_utils import get_or_create_dic
from .init_utils import init_vars, indicator
from .search_object import SearchObject


def multi_search_sug(n, query, group):
    r_list = []
    for i in indicator[n]:
        temp_list = list(init_vars.mdict_odict.values())[i]
        mdx = temp_list.mdx
        mdd_list = temp_list.mdd_list
        g_id = temp_list.g_id
        dict_file = mdx.get_fname()

        dic = get_or_create_dic(dict_file)
        if dic.mdict_enable:
            if group == 0:
                r_list.extend(SearchObject(mdx, mdd_list, dic, query).search_sug_entry(3))
            else:  # 查询某个词典分组下的词典
                for pk, name in dic.mdict_group.values_list():
                    if pk == group:
                        r_list.extend(SearchObject(mdx, mdd_list, dic, query).search_sug_entry(3))
                        break
    return r_list


def multi_search_mdx(n, query, group):
    r_list = []
    for i in indicator[n]:
        temp_list = list(init_vars.mdict_odict.values())[i]
        mdx = temp_list.mdx
        mdd_list = temp_list.mdd_list
        g_id = temp_list.g_id
        dict_file = mdx.get_fname()

        dic = get_or_create_dic(dict_file)

        if dic.mdict_enable:
            entry_list = []
            if group == 0:  # 默认查询全部词典
                entry_list = SearchObject(mdx, mdd_list, dic, query, g_id=g_id).search_mdx_entry()
            else:  # 查询某个词典分组下的词典
                for pk, name in dic.mdict_group.values_list():
                    if pk == group:
                        entry_list = SearchObject(mdx, mdd_list, dic, query, g_id=g_id).search_mdx_entry()

                        break

            r_list.extend(entry_list)
    return r_list
