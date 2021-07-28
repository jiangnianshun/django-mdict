#!/usr/bin/env python
import os
import sys
import asyncio
import json
import websockets

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

from mdict.mdict_utils.multi_process import multiprocess_search_mdx, create_process_pool, \
    get_cpu_num, pre_pool_search
from mdict.mdict_utils.object_coder import objectEncoder
from mdict.mdict_utils.init_utils import init_mdict_list
from mdict.mdict_utils.mdict_config import get_config_con

prpool = None

cnum = 1


async def ws_search(websocket, path):
    params = json.loads(await websocket.recv())
    query_list = params['query_list']
    if 'group' in params.keys():
        group = params['group']
    else:
        group = 0
    if 'query_type' in params.keys():
        query_type = params['query_type']
    else:
        query_type = 'dic'

    result_list = []

    if query_type == 'dic':
        q_list = ((i, query_list, group) for i in range(cnum))
        r_list = prpool.starmap(multiprocess_search_mdx, q_list)
    else:
        q_list = ((i, query_list, group, False) for i in range(cnum))
        r_list = prpool.starmap(multiprocess_search_mdx, q_list)
    for ri in r_list:
        result_list.extend(ri)

    if query_type == 'dic':
        result = json.dumps(result_list, cls=objectEncoder)
    else:
        result = json.dumps(result_list)

    await websocket.send(result)


if __name__ == '__main__':
    init_vars = init_mdict_list(False)
    prpool = create_process_pool()
    cnum = get_cpu_num()

    # pre_pool_search(prpool, init_vars)
    # windows下ws_server第一次查询时
    # 1.在asyncio内且各进程独自读取缓存，占用内存一直大于正常值但不到100%；
    # 2.在asyncio外且各进程独自读取缓存，内存和硬盘占用100%，一段时间后内存和硬盘占用恢复到正常值；
    # 3.在asyncio外且统一传入缓存，内存逐渐增加到100%再回归到正常值，硬盘无占用，但是启动时间相比与1和2大大增加。
    ws_server_port = get_config_con('ws_server_port')
    start_server = websockets.serve(ws_search, "localhost", ws_server_port)

    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    except OSError as e:
        print(e)
