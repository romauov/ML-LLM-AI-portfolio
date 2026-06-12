"""
Middleware для добавления префикса для пути

app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/api')

@author Sergey Goncharov
"""


# pylint: disable=too-few-public-methods
class PrefixMiddleware:
    """
    Добавление префикса для пути
    """

    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)

        start_response('404', [('Content-Type', 'text/plain')])
        return ["This url does not belong to the app.".encode()]
