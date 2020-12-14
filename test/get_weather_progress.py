import aiohttp
import asyncio

# https://openweathermap.org/current#severalid

url = 'http://localhost:7007'
request_ids = ['132e6d67-0424-49fe-88ad-c208d9d2ee62']

async def main():
    async with aiohttp.ClientSession() as session:
        try:
            for request_id in request_ids:
                async with session.get('{url}/weather/{rid}'.format(url=url, rid=request_id)) as resp:
                    print(await resp.text())
        except BaseException as  e:
            print(e)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())