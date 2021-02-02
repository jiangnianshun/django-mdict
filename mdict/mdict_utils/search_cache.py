from mdict.mdict_utils.mdict_config import get_config_con

_key_cache = {}

_sug_cache = {}


class CacheControllor:
    def __init__(self, cache, auto_clear=False):
        self.auto_clear = auto_clear
        self._cache = cache

    def put(self, query, group, dic_pk, data):
        if self.auto_clear:
            self.clear_full()
        self._cache[get_key(query, group, dic_pk)] = data

    def get(self, query, group, dic_pk):
        return self._cache.get(get_key(query, group, dic_pk))

    def delete(self, query, group, dic_pk):
        if get_key(query, group, dic_pk) in self._cache.keys():
            del self._cache[get_key(query, group, dic_pk)]

    def clear_full(self):
        if self.is_full():
            self._cache.clear()

    def is_full(self):
        cache_num = get_config_con('cache_num')
        return True if len(self._cache) >= cache_num else False


key_cache = CacheControllor(_key_cache)
sug_cache = CacheControllor(_sug_cache, auto_clear=True)


def get_key(query, group, dic_pk):
    return str(group) + ':' + str(dic_pk) + ':' + str(query)


class MdictPage:
    def __init__(self, query, group, data):
        self.query = query
        self.group = group

        self.page_size = 50
        self.max_page_size = 70

        self.total_count = len(data)
        if self.total_count % self.page_size <= self.max_page_size - self.page_size:
            if self.total_count < self.page_size:
                self.total_page = 1
            else:
                self.total_page = int(self.total_count / self.page_size)
        else:
            self.total_page = int(self.total_count / self.page_size) + 1

        self.finish = False  # 当前数据在分页中未被取完
        self.search_count = 0

        key_cache.put(query, group, -1, data)

    def get_ret(self, page):
        self.search_count += 1
        ret = {
            "page_size": self.page_size,  # 每页显示两个
            "total_count": self.total_count,  # 一共有多少数据
            "total_page": self.total_page,  # 一共有多少页
            "current_page": page,  # 当前页数
            "data": self.get_data(page),
            # "data": serializer.data,
        }
        return ret

    def get_data(self, page):
        data = key_cache.get(self.query, self.group, -1)
        if page <= 1:
            page = 1
            self.finish = False
        if self.total_page == 1:
            r_list = data
            self.finish = True
        else:
            if page == 1:
                r_list = data[:self.page_size]
            elif page == self.total_page:
                r_list = data[(page - 1) * self.page_size:]
                self.finish = True
            else:
                r_list = data[(page - 1) * self.page_size:page * self.page_size]

        return r_list

    def reduce(self):
        self.search_count -= 1

    def delete(self):
        key_cache.delete(self.query, self.group, -1)


class MdictPaginator:
    def __init__(self):
        self._pool = {}

    def put(self, page):
        if self.is_full():
            tmp = []
            for k in self._pool.keys():
                if self._pool[k].finish:
                    tmp.append(k)
            for k in tmp:
                if self._pool[k].search_count < 0:
                    self.delete(k)

        self._pool[get_key(page.query, page.group, -1)] = page

    def get(self, query, group):
        q = self._pool.get(get_key(query, group, -1))
        if q is None:
            return None

        for p in self._pool.keys():
            if p != query:
                self._pool[p].reduce()
        return q

    def list(self):
        txt = ''
        for k in self._pool.keys():
            txt += k
        return txt

    def delete(self, k):
        if k in self._pool.keys():
            self._pool[k].delete()
            del self._pool[k]

    def is_full(self):
        cache_num = get_config_con('search_cache_num')
        return True if len(self._pool) > cache_num else False


key_paginator = MdictPaginator()
es_paginator = MdictPaginator()
