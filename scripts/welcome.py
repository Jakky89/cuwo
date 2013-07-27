"""
Sends a welcome message to players
"""

from cuwo.script import ServerScript
from twisted.internet import reactor


class WelcomeServer(ServerScript):
    connection_class = None

    def on_load(self):
        config = self.server.config.base
        self.welcome = self.server.format_lines(config.welcome)
        self.help_players = config.help_players

    def on_new_connection(self, connection):
        connection.send_lines(self.welcome)
        reactor.callLater(10, connection.send_lines, self.help_players)


def get_class():
    return WelcomeServer
