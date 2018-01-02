from aiohttp import web
#from logs import log

async def test(request):
#    log.debug('test call')
    return web.Response(text='Test!')

async def hello(request):
#    log.debug('hello call')
    return web.Response(text='Hello!')
