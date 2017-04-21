from http.server import SimpleHTTPRequestHandler, HTTPServer
from watchdog.observers import Observer
from threading import Thread
from os.path import join


class ObserverEventHandler:
    def __init__(self, callback, server_object):
        self.callback = callback
        self.server = server_object

    def dispatch(self, event):
        self.callback()
        #self.server.did_update = True


def start_server(serve_path, ip, port, callback=None, observe_path='src'):

    class SiteHTTPRequestHandler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            return join(serve_path, path.lstrip('/'))

    server_address = (ip, port)
    httpd = HTTPServer(server_address, SiteHTTPRequestHandler)
    server_thread = Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    if callback is None:
        return

    observer = Observer()
    observer.schedule(ObserverEventHandler(callback, httpd), observe_path, recursive=True)
    observer.start()

    return server_thread, server_address
