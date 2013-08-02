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

    def on_new_connection(self, event):
        reactor.callLater(10, event.connection.send_lines, self.welcome)

def get_class():
    return WelcomeServer
