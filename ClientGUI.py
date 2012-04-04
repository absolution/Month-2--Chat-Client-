# Project: Community Coding Month 2: Server/Client Chat
# Author: Absolution
# Version: 2.0
# Client GUI

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *

from keyczar.keys import RsaPrivateKey
from keyczar.keys import RsaPublicKey

import asyncore
import asynchat
import socket
import threading
import sys
import Queue


class ClientConnection(asynchat.async_chat):

    def __init__(self, server, port, username, gui):
        asynchat.async_chat.__init__(self)
        self.username = username
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((server, port))
        self.gui = gui
        self.data = []
        self.set_terminator("\r\n")
        self.msgRecvd = Queue.Queue()

        self.session_keys = None
        self.public_key = None
        self.server_public_key = None
        self.create_session_keys()

    # On connection
    def handle_connect(self):
        # Send public key to server
        self.push(str(self.public_key) + "\r\n")

    # Handle closing of the socket
    def handle_close(self):
        self.close()

    def handle_excpt(self):
        self.msgRecvd.put(self.post_Message("Server could not be contacted."))
        self.close()

    # Handle information coming from the socket
    def collect_incoming_data(self, data):
        self.data.append(data)

    # Found self.set_terminator keyword
    def found_terminator(self):
        self.process_data()

    # Process the data before the terminator keyword
    def process_data(self):
        data = "".join(self.data)
        self.data = []

        # Check if client has server public key
        if not self.server_public_key:
            # Check if <data> is an RSA public key
            if data.find("publicExponent") != -1:
                # Set server public key
                self.set_server_public_key(data)
                # Send client's username
                self.send_username()
        # Else data will be encrypted
        else:
            # Decrypt data with client private key
            data = self.decrypt_data(data)
            # Check if data is the user list
            if data.startswith("ulist"):
                self.update_userlist(data)
            # Else data is chatter
            else:
                self.msgRecvd.put(self.post_Message(data))

    def update_userlist(self, data):
        # Strip userlist keyword from data
        userlist = data.split(":")[1]
        # Split users
        userlist = userlist.split(",")
        # Clear current GUI user list
        self.gui.qlwUsers.clear()
        # Add each user to GUI list
        for user in userlist:
            self.gui.qlwUsers.addItem(user.strip())

    # Sets the server public key when received
    def set_server_public_key(self, data):
        self.server_public_key = RsaPublicKey.Read(data.strip())

    # Send message encrypted with server public key
    def send_Message(self, message):
        encrypted_message = self.encrypt_data(message)
        self.push(encrypted_message + "\r\n")

    # Send username encrypted with server public key
    def send_username(self):
        username = "uname:%s" % (self.username)
        encrypted_uname = self.encrypt_data(username)
        self.push(encrypted_uname + "\r\n")

    # Send message to GUI thread to be placed in chat log
    def post_Message(self, message):
        return self.gui.Write_to_Log(message)

    # Create private/public key pair for chat session
    def create_session_keys(self):
        self.session_keys = RsaPrivateKey.Generate()
        self.public_key = self.session_keys.public_key

    # Encrypt data with server public key
    def encrypt_data(self, data):
        return self.server_public_key.Encrypt(data.encode("UTF-8"))

    # Decrypt data with client private key
    def decrypt_data(self, data):
        return self.session_keys.Decrypt(data)


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
        self.twOptions = self.widget.findChild(QTabWidget, "twOptions")
            # Menu Items
        self.menuConnect = self.widget.findChild(QAction, "menuConnect")
        self.menuDisconnect = self.widget.findChild(QAction, "menuDisconnect")
        self.menuExit = self.widget.findChild(QAction, "menuQuit")
            # List Widget
        self.qlwUsers = self.widget.findChild(QListWidget, "qlwUsers")
            # Text Boxes
        self.teChatLog = self.widget.findChild(QTextEdit, "teChatLog")
        self.leUsername = self.widget.findChild(QLineEdit, "leUsername")
        self.leServerIP = self.widget.findChild(QLineEdit, "leServerIP")
        self.leServerPort = self.widget.findChild(QLineEdit, "leServerPort")
        self.leMessage = self.widget.findChild(QLineEdit, "leMessage")
            # Push Buttons
        self.pbSend = self.widget.findChild(QPushButton, "pbSend")
        self.pbConnect = self.widget.findChild(QPushButton, "pbConnect")
        self.pbDisconnect = self.widget.findChild(QPushButton, "pbDisconnect")
        self.pbExit = self.widget.findChild(QPushButton, "pbExit")
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
        self.startClient.client.send_Message(self.leMessage.text())
        self.teChatLog.append("%s: %s" % (self.username, self.leMessage.text()))
        self.leMessage.setText("")

    def Write_to_Log(self, data):
        self.teChatLog.append(data)

ChatClientGUI()
