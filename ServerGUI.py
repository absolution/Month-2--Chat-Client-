# Project: Community Coding Month 2: Server/Client Chat
# Author: Absolution
# Version: 1.0
# Server GUI

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *
import asyncore
import socket
import threading
import Queue
import sys


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
                self.server.write_gui.put(self.server.write_to_gui_log("%s connected." % (self.username)))
            else:
                datatosend = "%s: %s" % (self.username, data)
                self.server.write_gui.put(self.server.write_to_gui_log(datatosend))
                self.server.broadcast(datatosend, self)

    def handle_close(self):
        self.server.write_gui.put(self.server.write_to_gui_log("%s left." % (self.username)))
        asyncore.dispatcher_with_send.handle_close(self)
        self.server.client_disconnect(self)


class ConnectionHandler(asyncore.dispatcher):

    def __init__(self, host, port, gui):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        self.clients = []
        self.gui = gui
        self.write_gui = Queue.Queue()
        startText = "Server Started on: %s @ %s" % (host, port)
        self.write_gui.put(self.write_to_gui_log(startText))

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            pass
        else:
            sock, addr = pair
            self.clients.append(Messenger(self, sock))

    def broadcast(self, text, sender):
        for client in self.clients:
            if client != sender:
                client.send(text)

    def client_disconnect(self, client):
        self.clients.remove(client)

    def write_to_gui_log(self, data):
        return self.gui.Write_Log(data)

    def shutdown(self):
        for client in self.clients:
            client.close()

    def handle_close(self):
        self.close()


class Server_Thread(threading.Thread):

    def __init__(self, host, port, gui):
        threading.Thread.__init__(self)
        self.server = ConnectionHandler(host, port, gui)

    def run(self):
        asyncore.loop()

    def stop(self):
        #self.server.shutdown()
        self.server.handle_close()


class ChatServerGUI(object):

    def __init__(self):

        # Create Application
        self.app = QApplication([])

        # Create the UI Loader
        self.loader = QUiLoader()

        # Load the UI file
        self.widget = self.loader.load("./GUI/servergui.ui")
        self.widget.setWindowTitle("Chat Server - by Absolution")
        self.widget.show()

        # Associate UI Elements
            # Menu Items
        self.menuListen = self.widget.findChild(QAction, 'menuListen')
        self.menuExit = self.widget.findChild(QAction, 'menuQuit')
            # Text Edit
        self.teActivity = self.widget.findChild(QTextEdit, 'teActivity')
            # Buttons
        self.pbListen = self.widget.findChild(QPushButton, 'pbListen')
        self.pbExit = self.widget.findChild(QPushButton, 'pbExit')
        # Connect Objects to Functions
            # Menu Items
        #self.menuExit.triggered.connect(self.ExitApp())
            # Buttons
        self.pbListen.clicked.connect(self.Start_Server)
        self.pbExit.clicked.connect(self.ExitApp)

        # Launch Application
        self.app.exec_()

    ## Exit App
    def ExitApp(self):
        self.server.stop()
        sys.exit(0)

    def Start_Server(self):
        self.server = Server_Thread("localhost", 8192, self)
        self.server.start()

    def Write_Log(self, data):
        self.teActivity.append(data)

ChatServerGUI()
