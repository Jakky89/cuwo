from cuwo.script import (FactoryScript, ProtocolScript, command, get_player)
from twisted.web import server, resource
from twisted.internet import reactor
import json


class WebProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.connections.append(self)

    def dataReceived(self, data):
        data = json.loads(data)
        print data
        if data['want'] == 'players':
            self.transport.write(self.factory.get_players())
        else:
            self.transport.write(json.dumps({'response': "This shit got serious"}))

    def connectionLost(self, reason):
        self.factory.connections.remove(self)


class WebFactory(Factory):
    def __init__(self, server):
        self.connections = []
        self.server = server

    def get_players(self):
        ##list = [names[],levels[],class[],[specializations[]]
        list = [[], [], [], []]
        for connection in self.server.connections.values():
            print connection.entity_data.name
            list[0].append(connection.entity_data.name)
            list[1].append(connection.entity_data.character_level)
            list[2].append(connection.entity_data.class_type)
            list[3].append(connection.entity_data.specialization)
        players = {'response': 'players', 'names': list[0], 'levels': list[1], 'klass': list[2], 'specialz': list[3]}
        return json.dumps(players)

    def buildProtocol(self, addr):
        return WebProtocol(self)


class WebScriptProtocol(ProtocolScript):

    """


    def on_chat(self, message):
        message = message.encode('ascii', 'replace')
        message = '<%s> %s' % (self.protocol.name(), message)
        self.parent.send(message)
    """

    def on_join(self):
        self.parent.update_web("players")

    def on_unload(self):
        self.parent.update_web("players")

class WebScriptFactory(FactoryScript):
    protocol_class = WebScriptProtocol

    def on_load(self):
        self.connections = []
        self.web_factory = WebFactory(self.factory)
        reactor.listenTCP(self.factory.config.web_port, WebSocketFactory(self.web_factory))

    def update_web(self, entity):
        if entity == "players":
            for connection in self.web_factory.connections:
                connection.transport.write(self.web_factory.get_players())
            return
        pass


def get_class():
    return WebScriptFactory
