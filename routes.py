from txtprocessor import test
from txtprocessor import hello

def setup_routes(app):
    app.router.add_get('/', test)
    app.router.add_get('/h', hello)
