import os, pickle, pkg_resources
from copy import deepcopy

# 来源http://kaifangcidian.com/han/chaizi/
# 不存在的字
# 上开下木、这个在中华字海中查不到
# 左山右鸟，
# 显示为□，unicode码25A1，处理的时候可以去掉。

# 已完成
# 阞-耳力
# 囡-口女
# 邗-干耳
# 笹-竹世
# 嶋嶌-山鳥
# 魇-厂犬鬼
# 藠-草白白白
# 暦-厂林日，厂木木日
# 昃-日仄，日厂人
# 皨-白白白土
# 笹-竹世
# 嶋嶌-山鳥

# 待完成
# 晷-日咎，日久人口，日处口？
# 翕-合羽，合习习，人一口羽？
# 上竹下吴

# 仅支持原本的偏旁，不会对偏旁进行繁简转化，比如纟替换成丝，但糹就不会替换成絲，但是可以通过繁简转化时将絲替换成丝，再查到纟
# 这里偏旁的简繁和查询时的简繁比较混乱，后面再处理
# 这里只用了一层替换，是否需要多层替换
# 繁体偏旁在查询时处理，还是在word_replace_dict这里处理
word_replace_dict = {'囗': '口', '阝': '耳', '礻': '示', '衤': '衣', '冫': '水', '氵': '水', '灬': '水', '讠': '言', '訁': '言',
                     '刂': '刀', '卩': '刀', '亻': '人', '彳': '人', '艹': '草', '纟': '丝', '糹': '丝', '牜': '牛',
                     '钅': '金', '釒': '金', '⺮': '竹', '忄': '心', '扌': '手', '丬': '将', '爿': '将', '': '韩', '疒': '病',
                     '辶': '之', '廴': '建', '犭': '犬', '飠': '食', '饣': '食', '': '春', '宀': '宝', '冖': '宝',
                     '亠': '京', '癶': '登', '凵': '框', '冂': '框', '匚': '框', '匸': '框', '勹': '包',
                     '罒': '四', '覀': '西', '襾': '西'}
redundant_word_list = ['一', '㇆', '丿', '乀', '丨', '乚', '厶', '乁', '爫', '丶', '乛', '丷',
                       '夂', '廾', '彡', '巛', '虍', '隹', '辵', '艸', '𢦏', '戸', '乂', '冎',
                       '彐', '疋', '殳', '彑', '屰', '丅', '叀', '\uf7ee', '冃', '㇉', '𤇾', '龴', '攴', '糸']


# 表-丰，\uf7ee，\uf7ee是表的下半部分，不在unicode中

class HanziChaizi(object):
    def __init__(self):
        data_file = pkg_resources.resource_filename(__name__, "data/data.pkl")

        with open(data_file, 'rb') as fd:
            self.data = pickle.load(fd)

        reverse_data_file = pkg_resources.resource_filename(__name__, "data/reverse_data.pkl")

        if os.path.exists(reverse_data_file):
            with open(reverse_data_file, 'rb') as fd:
                self.reverse_data = pickle.load(fd)

    def add_new_chaizi(self, new_word):
        key = list(new_word.keys())[0]
        print(new_word)

        data_original_file = pkg_resources.resource_filename(__name__, "data/data_original.pkl")

        with open(data_original_file, 'rb') as fd:
            data_original = pickle.load(fd)

        if key in data_original.keys():
            old_word = data_original[key]
            old_word.extend(new_word[key])
            new_dict = {key: old_word}
            print(old_word, new_dict)
            data_original.update(new_dict)
        else:
            data_original.update(new_word)

        with open(data_original_file, 'wb') as fd:
            pickle.dump(data_original, fd)

    def convert_original(self):
        data_original_file = pkg_resources.resource_filename(__name__, "data/data_original.pkl")

        with open(data_original_file, 'rb') as fd:
            data_original = pickle.load(fd)

        data_original_key_list = list(data_original.keys())
        for i in range(len(data_original) - 1, -1, -1):
            ikey = data_original_key_list[i]
            if ikey == '□':  # 无法显示的键
                del data_original[ikey]
                continue

            list_out = data_original[ikey]
            list_out_len = len(list_out)
            for j in range(list_out_len - 1, -1, -1):
                list_in = list_out[j]
                insert_list = []
                new_chaizi_list = []

                for k in range(len(list_in)):

                    word = list_in[k]
                    if type(word) != str:
                        del list_out[j]
                        continue

                    if word == '□':  # 无法显示的拆字
                        del data_original[ikey]
                        continue

                    if word in word_replace_dict.keys():
                        if new_chaizi_list:
                            new_chaizi_list = [word_replace_dict[word] if i == word else i for i in new_chaizi_list]
                        else:
                            new_chaizi_list = [word_replace_dict[word] if i == word else i for i in list_in]

                    redundant_flag = False
                    for t_word in list_in:
                        if t_word in redundant_word_list:
                            redundant_flag = True
                            break
                    if not redundant_flag:
                        r_chaizi = self.query(word)
                        if r_chaizi is not None:

                            for rc_list in r_chaizi:

                                for rc in rc_list:
                                    if rc in redundant_word_list or rc in word_replace_dict.keys():
                                        redundant_flag = True
                                        break
                                if not redundant_flag:

                                    new_chaizi_list2 = deepcopy(list_in)
                                    # 这里要深拷贝，否则只是引用，修改的是原体，不是复制体

                                    temp_k = k
                                    del new_chaizi_list2[k]
                                    for m in range(len(r_chaizi[0])):
                                        new_chaizi_list2.insert(temp_k, r_chaizi[0][m])
                                        temp_k += 1
                                    if new_chaizi_list2 not in insert_list:
                                        insert_list.append(new_chaizi_list2)

                if new_chaizi_list:
                    insert_list.append(new_chaizi_list)
                if insert_list:

                    for new_chaizi in insert_list:
                        if new_chaizi not in list_out:
                            list_out.append(new_chaizi)
                            data_original[ikey] = list_out

        # 修改data_original

        data_file = pkg_resources.resource_filename(__name__, "data/data.pkl")

        with open(data_file, 'wb') as fd:
            pickle.dump(data_original, fd)

    def convert_reverse(self):  # 将data.pkl转化为reverse_data.pkl
        reverse_dict = {}
        ex = self.data

        for k in ex.keys():

            for chaizi_list in ex[k]:  # 处理每一个拆字序列
                zi_dict = {}
                for i in range(len(chaizi_list) - 1, -1, -1):

                    if i >= 1:
                        if i == len(chaizi_list) - 1:
                            temp_dict = {chaizi_list[i]: {'r': [k]}}

                            zi_dict[chaizi_list[i - 1]] = temp_dict


                        else:

                            zi_dict[chaizi_list[i - 1]] = deepcopy(zi_dict)
                            if chaizi_list[i] != chaizi_list[i - 1]:
                                del zi_dict[chaizi_list[i]]
                            # 这里需要深度拷贝
                reverse_dict = self.insert_hanzi(reverse_dict, zi_dict)

        reverse_data_file = pkg_resources.resource_filename(__name__, "data/reverse_data.pkl")
        with open(reverse_data_file, 'wb') as fd:
            pickle.dump(reverse_dict, fd)

    def insert_hanzi(self, reverse_dict, zi_dict):
        for zk in zi_dict.keys():
            if zk in reverse_dict.keys():
                if zk != 'r':
                    reverse_dict[zk] = self.insert_hanzi(reverse_dict[zk], zi_dict[zk])
                else:
                    reverse_dict[zk].extend(zi_dict[zk])
            #         比如伞和什的拆字都是人，十，因此一样的拆字结果可能是不同的汉字
            # 比如言和訁都是丶 一 二 口
            else:
                reverse_dict.update(zi_dict)
        return reverse_dict

    def query(self, input_char, default=None):
        return self.data.get(input_char, default)

    def reverse_query(self, query):
        self.counter = 0
        return self.r_query1(self.reverse_data, query)

    def r_query1(self, query_dict, query, check=True):
        for q in query:
            if q in query_dict.keys():
                if len(query) == 1:
                    if 'r' in query_dict[q].keys():
                        return query_dict[q]['r']
                    else:
                        return []
                return self.r_query1(query_dict[q], query[1:])
            else:
                return []
