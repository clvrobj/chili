#!/usr/bin/python
from flup.server.fcgi import WSGIServer
from chili import app

if __name__ == '__main__':
    WSGIServer(app, bindAddress='/tmp/chili-fcgi.sock').run()
    #WSGIServer(app).run()
