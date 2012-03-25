import asyncore
import socket
import threading
import sys


class ClientConnection(asyncore.dispatcher_with_send):

    def __init__(self, server, port, username):
        asyncore.dispatcher_with_send.__init__(self)
        self.username = username
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((server, port))
        self.buffer = ''

    def handle_connect(self):
        sendUname = "uname:%s" % (self.username)
        self.send(sendUname)

    def handle_close(self):
        self.close()

    def handle_read(self):
        data = self.recv(8192)
        if data:
            print data

    def send_Message(self, message):
        self.send(message)


class ClientThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.client = ClientConnection("localhost", 8192, "absolution")

    def run(self):
        asyncore.loop()

startClient = ClientThread()
startClient.start()

connected = True
while connected:
    message = raw_input(">> ")
    startClient.client.send_Message(message)

sys.exit(0)
