#!/usr/bin/env python
import asyncio
import websockets
import json

from mdict.mdict_utils.object_coder import objectDecoder


async def search(entry):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri, max_size=100000000) as websocket:
        # entry = input("search entry:")

        await websocket.send(entry)

        result = await websocket.recv()
        result_list = json.loads(result, object_hook=objectDecoder)


asyncio.get_event_loop().run_until_complete(search('a'))
