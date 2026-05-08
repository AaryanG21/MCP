import asyncio, websockets, json
async def test():
    async with websockets.connect('ws://localhost:8765') as ws:
        await ws.send(json.dumps({'prompt': 'Find details of Tesla, Inc. using fetch_company_data'}))
        await asyncio.sleep(5)
        await ws.send(json.dumps({'prompt': 'Get data for Google from internet'}))
        await asyncio.sleep(5)
asyncio.run(test())
