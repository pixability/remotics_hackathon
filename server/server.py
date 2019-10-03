#!/usr/bin/env python3

import uuid

from tornado import ioloop
import tornado.web
import tornado.websocket
import tornado.template
import json


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', WebSocketHandler),
        ]
        settings = dict(debug=True)
        tornado.web.Application.__init__(self, handlers, **settings)
        print("Server Ready")


class Controller:
    def call_method(self, arg, payload, connection):
        method = getattr(self, arg)
        return method(payload, connection)

    def depress(self, keyType, conn):
        print('called depress')
        print(keyType)
        message = self.get_message(keyType)
        conn.write_message(message)

    def press(self, keyType, conn):
        print('called press')
        print(keyType)
        message = self.get_message(keyType)
        conn.write_message(message)

    def get_message(self, keyType):
        if keyType == 'U':
            return 'd 100 0'
        elif keyType == 'R':
            return 'd 100 -90'
        elif keyType == 'L':
            return 'd 100 90'
        elif keyType == 'D':
            return 'd -100 0'
        elif keyType == 'A':
            return 'v'
        else:
            return 's'

class Connection:
    def __init__(self, conn, client_id, client_type):
        self.conn = conn
        self.client_id = client_id
        self.client_type = client_type


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    connections = set()
    robot_connection = set()
    controller = Controller()

    def subscribe(self, message):
        payload = message.get('payload')

        if type(payload) == str:
            payload = json.loads(payload)

        client_type = payload.get('type')
        client_id = str(uuid.uuid4())
        connection = Connection(self, client_id, client_type)

        if client_type == 'robot':
            # only allowing one robot
            if not self.robot_connection:
                self.robot_connection.add(connection)
            else:
                self.robot_connection.clear()
                self.robot_connection.add(connection)

            message = json.dumps(
                {'module': 'connections', 'operation': 'subscribeSuccess', 'payload': {'client_id': client_id}})
            self.write_message(message)
        elif client_type == 'controller':
            self.connections.add(connection)
            message = json.dumps(
                {'module': 'connections', 'operation': 'subscribeSuccess', 'payload': {'client_id': client_id}})
            self.write_message(message)

            if len(self.connections) > 1:
                for connection in self.connections:
                    message = json.dumps(
                        {'module': 'connections', 'operation': 'updateTotalConnections', 'payload': {'count': num_con}})

    def check_origin(self, origin):
        return True

    def open(self):
        print('connection opened...')

    def on_close(self):
        print("A client disconnected")
        for item in self.connections:
            print(item.client_id)
            if item.client_type == 'robot' and len(self.robot_connection) > 0 and item.conn == self:
                self.robot_connection.remove(item)
                print("Removed Robot ID: {}", item.client_id)
                return
            elif item.client_type == 'controller' and item.conn == self:
                self.connections.remove(item)
                print("Removed Controller ID: {}", item.client_id)
                return

    def get_connection(self, id):
        for x in self.connections:
            if x.get('client_id') == id:
                return x.get('conn')

    def on_message(self, message):
        print('received:', message)
        if message != 'keep alive':
            message_dict = json.loads(message)

            if message_dict.get('module') == 'controller':
                if self.robot_connection:
                    robot = next(iter(self.robot_connection))
                    self.controller.call_method(message_dict.get('operation'), message_dict.get('payload').get('key'),
                                                robot.conn)
                if len(self.connections) > 1:
                    for item in self.connections:
                        if item.conn != self:
                            item.conn.send_message(message)

            elif message_dict.get('module') == 'connections':
                if message_dict.get('operation') == 'subscribe':
                    self.subscribe(message_dict)


def main():
    app = Application()
    app.listen(3030)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
