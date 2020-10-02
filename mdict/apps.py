from django.apps import AppConfig

from mdict.mdict_utils.init_utils import init_mdict_list


# 启动mdict时进行初始化
class MdictConfig(AppConfig):
    name = 'mdict'

    def ready(self):
        init_mdict_list(False)
