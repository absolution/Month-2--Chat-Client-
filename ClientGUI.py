# Project: Community Coding Month 2: Server/Client Chat
# Author: Absolution
# Version: 1.0
# Client GUI

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *
import asyncore
import socket
import threading
import sys
import Queue


class ClientConnection(asyncore.dispatcher_with_send):

    def __init__(self, server, port, username, gui):
        asyncore.dispatcher_with_send.__init__(self)
        self.username = username
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((server, port))
        self.gui = gui
        self.msgRecvd = Queue.Queue()

    # On connection send the username
    def handle_connect(self):
        sendUname = "uname:%s" % (self.username)
        self.send(sendUname)

    # Handle closing of the socket
    def handle_close(self):
        print "closing"
        self.close()

    # Handle information coming from the socket
    def handle_read(self):
        data = self.recv(8192)
        if data:
            lines = data.split('\n')
            for line in lines:
                if line.startswith("ulist"):
                    line = line.split(':')
                    users = line[1].split(',')
                    self.gui.qlwUsers.clear()
                    for user in users:
                        self.gui.qlwUsers.addItem(user.strip())
                else:
                    if line.strip() != '':
                        self.msgRecvd.put(self.post_Message(line))

    # Send message to the server
    def send_Message(self, message):
        self.send(message)

    # Send message to GUI thread to be placed in chat log
    def post_Message(self, message):
        return self.gui.Write_to_Log(message)


class ClientThread(threading.Thread):

    # Start the thread for the socket
    def __init__(self, server, port, user, gui):
        threading.Thread.__init__(self)
        self.client = ClientConnection(server, int(port), user, gui)

    # Run the asyncore loop
    def run(self):
        try:
            asyncore.loop()
        except:
            return 0


class ChatClientGUI(object):

    def __init__(self):

        # Create Application
        self.app = QApplication([])

        # Create the UI Loader
        self.loader = QUiLoader()

        # Load the UI file
        self.widget = self.loader.load("./GUI/clientgui.ui")
        self.widget.setWindowTitle("Chat Client - by Absolution")
        self.widget.show()

        self.startClient = None
        self.username = None

        # Associate UI Elements
            # Tab Widget
        self.twOptions = self.widget.findChild(QTabWidget, 'twOptions')
            # Menu Items
        self.menuConnect = self.widget.findChild(QAction, 'menuConnect')
        self.menuDisconnect = self.widget.findChild(QAction, 'menuDisconnect')
        self.menuExit = self.widget.findChild(QAction, 'menuQuit')
            # List Widget
        self.qlwUsers = self.widget.findChild(QListWidget, 'qlwUsers')
            # Text Boxes
        self.teChatLog = self.widget.findChild(QTextEdit, 'teChatLog')
        self.leUsername = self.widget.findChild(QLineEdit, 'leUsername')
        self.leServerIP = self.widget.findChild(QLineEdit, 'leServerIP')
        self.leServerPort = self.widget.findChild(QLineEdit, 'leServerPort')
        self.leMessage = self.widget.findChild(QLineEdit, 'leMessage')
            # Push Buttons
        self.pbSend = self.widget.findChild(QPushButton, 'pbSend')
        self.pbConnect = self.widget.findChild(QPushButton, 'pbConnect')
        self.pbDisconnect = self.widget.findChild(QPushButton, 'pbDisconnect')
        self.pbExit = self.widget.findChild(QPushButton, 'pbExit')
        # Connect Objects to Functions
            # Push Buttons
        self.pbConnect.clicked.connect(self.ConnectServer)
        self.pbDisconnect.clicked.connect(self.DisconnectServer)
        self.pbSend.clicked.connect(self.SendMessage)
        self.pbExit.clicked.connect(self.ExitApp)
            # Menu Items
        self.menuConnect.triggered.connect(self.ConnectServer)
        self.menuDisconnect.triggered.connect(self.DisconnectServer)
        self.menuExit.triggered.connect(self.ExitApp)

        # Launch Application
        self.app.exec_()

    # Exit App
    def ExitApp(self):
        try:
            self.startClient.client.close()
        except:
            pass
        sys.exit(0)

    def ConnectServer(self):
        server = self.leServerIP.text()
        port = self.leServerPort.text()
        self.username = self.leUsername.text()
        self.startClient = ClientThread(server, port, self.username, self)
        self.startClient.start()
        self.twOptions.setCurrentIndex(0)

    def DisconnectServer(self):
        self.startClient.client.close()
        self.startClient.join()
        self.teChatLog.append("You have disconnected from %s" % (self.leServerIP.text()))
        self.twOptions.setCurrentIndex(0)

    def SendMessage(self):
        self.startClient.client.send_Message(self.leMessage.text() + "\n")
        self.teChatLog.append("%s: %s" % (self.username, self.leMessage.text()))
        self.leMessage.setText("")

    def Write_to_Log(self, data):
        self.teChatLog.append(data)

ChatClientGUI()
