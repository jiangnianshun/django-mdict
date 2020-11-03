from .data_utils import get_or_create_dic, get_all_dic
from .init_utils import init_vars, indicator
from .search_object import SearchObject

values_list = list(init_vars.mdict_odict.values())

dics_list = get_all_dic()


def multi_search_mdx(n, query, group, is_mdx=True):
    r_list = []
    for i in indicator[n]:
        temp_object = values_list[i]
        mdx = temp_object.mdx
        mdd_list = temp_object.mdd_list
        g_id = temp_object.g_id
        dict_file = mdx.get_fname()

        dic_list = dics_list.filter(mdict_file=dict_file)
        if len(dic_list) == 0:
            dic = get_or_create_dic(dict_file)
        else:
            dic = dic_list[0]

        if dic.mdict_enable:
            if group == 0:  # 默认查询全部词典
                if is_mdx:
                    r_list.extend(SearchObject(mdx, mdd_list, dic, query, g_id=g_id).search_mdx_entry())
                else:
                    r_list.extend(SearchObject(mdx, mdd_list, dic, query).search_sug_entry(3))
            else:  # 查询某个词典分组下的词典
                for pk, name in dic.mdict_group.values_list():
                    if pk == group:
                        if is_mdx:
                            r_list.extend(SearchObject(mdx, mdd_list, dic, query, g_id=g_id).search_mdx_entry())
                        else:
                            r_list.extend(SearchObject(mdx, mdd_list, dic, query).search_sug_entry(3))
                        break
    return r_list
