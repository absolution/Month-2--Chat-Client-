import asyncore
import socket


class Messenger(asyncore.dispatcher_with_send):

    def __init__(self, server, sock):
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.server = server
        self.username = ''
        self.send("Server: Welcome to the server.")

    def handle_read(self):
        data = self.recv(8192)
        if data:
            if data.strip().startswith('uname:'):
                username = data.strip()
                username = username.split(':')
                self.username = username[1]
                print "%s Connected." % (self.username)
            else:
                datatosend = "%s: %s" % (self.username, data)
                print datatosend
                self.server.broadcast(datatosend, self)

    def handle_close(self):
        asyncore.dispatcher_with_send.handle_close(self)
        self.server.client_disconnect(self)


class ConnectionHandler(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        self.clients = []
        startText = "Server Started on: %s @ %s" % (host, port)
        print startText

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            pass
        else:
            sock, addr = pair
            connText = "Incoming connection from: %s" % (repr(addr))
            print connText
            self.clients.append(Messenger(self, sock))

    def handle_read(self):
        data, addr = self.recvfrom(8192)
        print str(addr) + " >> " + data

    def broadcast(self, text, sender):
        for client in self.clients:
            if client != sender:
                client.send(text)

    def client_disconnect(self, client):
        self.clients.remove(client)
        print self.clients


ConnectionHandler("localhost", 8192)
asyncore.loop()
