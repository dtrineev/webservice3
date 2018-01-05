from aiohttp import web
from txtprocessor import test
from routes import setup_routes

app = web.Application()
setup_routes(app)
#log.debug('Start server')
#web.run_app(app, host='127.0.0.1', port=8080)
web.run_app(app)

