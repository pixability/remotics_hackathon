#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen
from tornado.websocket import websocket_connect
import json


class DummyException(Exception):
    pass


class Client(object):
    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout
        self.ioloop = IOLoop.instance()
        self.ws = None
        self.connect()
        PeriodicCallback(self.keep_alive, 20000).start()
        self.ioloop.start()

    def _parse_response(self, response):
        if response.code == 418:
            raise DummyException
        return response

    @gen.coroutine
    def connect(self):
        print("trying to connect")
        try:
            resp = yield websocket_connect(self.url)
            self.ws = resp
        except Exception as e:
            result = self._parse_response(e)
            raise gen.Return(result)
        else:
            print("connected")
            message = json.dumps({"module": "connections", "operation": "press", "payload": {'client_type': 'controller'}})
            self.ws.write_message(message)
            message = json.dumps({"module": "controller", "operation": "press", "payload": {'key': 'u'}})
            self.ws.write_message(message)
        self.run()

    @gen.coroutine
    def run(self):
        while True:
            msg = yield self.ws.read_message()
            if msg is None:
                print("connection closed")
                self.ws = None
                break
            else:
                print(msg)

    def keep_alive(self):
        if self.ws is None:
            self.connect()
        else:
            self.ws.write_message("keep alive")
            message = json.dumps({"module": "controller", "operation": "press", "payload": {'key': 'u'}})
            self.ws.write_message(message)


if __name__ == "__main__":
    client = Client("ws://localhost:3030", 5)