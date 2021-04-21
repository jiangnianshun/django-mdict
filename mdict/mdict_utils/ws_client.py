#!/usr/bin/env python
import asyncio
import websockets
import json

from mdict.mdict_utils.object_coder import objectDecoder


async def search(query_list):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri, max_size=100000000) as websocket:
        # entry = input("search entry:")
        await websocket.send(json.dumps(query_list))

        result = await websocket.recv()
        result_list = json.loads(result, object_hook=objectDecoder)
        return result_list


def ws_search(query_list):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # 在django中调用时需要设置loop
    return asyncio.get_event_loop().run_until_complete(search(query_list))
