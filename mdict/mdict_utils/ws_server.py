#!/usr/bin/env python
import asyncio
import json
import websockets

from mdict.mdict_utils.multi_process import multiprocess_search_mdx, create_process_pool, get_cpu_num
from mdict.mdict_utils.init_utils import init_mdict_list
from mdict.mdict_utils.object_coder import objectEncoder

prpool = None

cnum = 1


async def ws_search(websocket, path):
    entry = await websocket.recv()

    record_list = []

    query_list = [entry]
    group = 0

    q_list = ((i, query_list, group) for i in range(cnum))
    a_list = prpool.starmap(multiprocess_search_mdx, q_list)
    for a in a_list:
        record_list.extend(a)

    result = json.dumps(record_list, cls=objectEncoder)
    await websocket.send(result)


if __name__ == '__main__':
    init_mdict_list(False)
    prpool = create_process_pool()
    cnum = get_cpu_num()

    start_server = websockets.serve(ws_search, "localhost", 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
