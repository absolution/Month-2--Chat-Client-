# Project: Community Coding Month 2: Server/Client Chat
# Author: Absolution
# Version: 2.0
# Server GUI

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *

from keyczar.keys import RsaPrivateKey
from keyczar.keys import RsaPublicKey

import asyncore
import asynchat
import socket
import threading
import Queue
import sys


class Messenger(asynchat.async_chat):

    def __init__(self, server, sock):
        asynchat.async_chat.__init__(self, sock)
        self.server = server
        self.set_terminator("\r\n")

        self.data = []
        self.username = ""
        self.client_public_key = None
        self.response = []

    # Handle the information coming into the socket
    def collect_incoming_data(self, data):
        self.data.append(data)

    # Found self.set_terminator keyword
    def found_terminator(self):
        print "Found terminator"
        self.process_data()

    # Process the data before the terminator keyword
    def process_data(self):
        data = "".join(self.data)
        self.data = []

        # Check if client public key has been received
        if not self.client_public_key:
            # Check if data is an RSA public key
            if data.find("publicExponent") != -1:
                # Set client public key
                self.set_client_public_key(data)
                # Send server public key
                self.send_public_key()
        # Else data will be encrypted
        else:
            # Decrypt data with server private key
            data = self.decrypt_data(data)
            # Check if data is a username
            if data.startswith("uname"):
                # Set client username
                self.set_username(data)
                # Send encrypted MOTD
                self.send_MOTD()
            # Else data is chatter
            else:
                datatosend = "%s: %s" % (self.username, data)
                self.server.write_gui.put(self.server.write_to_gui_log(datatosend))
                self.server.broadcast(datatosend, self)

    def set_username(self, data):
        # Strip whitespace from <data>
        username = data.strip()
        # Split keyword from data
        self.username = username.split(":")[1]
        # Append username to list of usernames
        self.server.usernames.append(self.username)
        # Write information to chat log GUI element
        self.server.write_gui.put(self.server.write_to_gui_log("%s connected." % (self.username)))
        # Send user list
        self.server.send_userlist()
        # Send user joined message
        self.server.broadcast("%s joined the chat." % (self.username), self)

    # Sets the client public key when received
    def set_client_public_key(self, data):
        self.client_public_key = RsaPublicKey.Read(data.strip())

    # Handle client leaving the chat
    def handle_close(self):
        # Write client that has left to chat log
        self.server.write_gui.put(self.server.write_to_gui_log("%s left." % (self.username)))
        # Broadcast client leaving to other clients
        self.server.broadcast("%s left the chat.\n" % (self.username), self)
        # Remove client username from global list
        if self.username in self.server.usernames:
            self.server.usernames.remove(self.username)
        # Remove client instance from the client instance list
        if self in self.server.clients:
            self.server.client_disconnect(self)
        # Send userlist to connected clients
        self.server.send_userlist()
        # Close socket
        self.close()

    # On client connection send the user list and send MOTD
    def send_MOTD(self):
        MOTD = self.encrypt_data(self.server.MOTD)
        self.push(str(MOTD) + "\r\n")

    # Encrypt data using client public key and send (global)
    def send_encrypted_data(self, data):
        encrypt_data = self.encrypt_data(data)
        self.push(str(encrypt_data) + "\r\n")

    # Send server public key
    def send_public_key(self):
        self.push(str(self.server.public_key) + "\r\n")

    # Encrypt data with client public key (instance)
    def encrypt_data(self, data):
        return self.client_public_key.Encrypt(data.encode("UTF-8"))

    # Decrypt data with server private key
    def decrypt_data(self, data):
        return self.server.session_keys.Decrypt(data)


class ConnectionHandler(asyncore.dispatcher):

    def __init__(self, host, port, gui):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        self.gui = gui
        self.write_gui = Queue.Queue()

        startText = "Server Started on: %s @ %s" % (host, port)
        self.write_gui.put(self.write_to_gui_log(startText))

        self.MOTD = "Welcome to the server."
        self.clients = []
        self.usernames = []

        self.session_keys = ""
        self.public_key = ""
        self.create_session_keys()

    # Handle incoming connection from client
    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            pass
        else:
            sock, addr = pair
            # Add instance to client instance list
            self.clients.append(Messenger(self, sock))

    # Generate public/private keys
    def create_session_keys(self):
        self.session_keys = RsaPrivateKey.Generate()
        self.public_key = self.session_keys.public_key

    # Broadcast <text> to all connected clients except <sender>
    def broadcast(self, text, sender):
        if self.usernames != None:
            for client in self.clients:
                if client != sender:
                    client.send_encrypted_data(text)

    # Send the client username list to all connected clients
    def send_userlist(self):
        ulist = "ulist:%s" % (",".join(self.usernames))
        for client in self.clients:
            # Encrpt using client public key and send
            client.send_encrypted_data(ulist)

    # Remove client instance on disconnection of client
    def client_disconnect(self, client):
        self.clients.remove(client)

    # Write data to GUI chat log element
    def write_to_gui_log(self, data):
        return self.gui.Write_Log(data)

    # Close all client sockets
    def shutdown(self):
        for client in self.clients:
            client.close()

    def handle_close(self):
        self.close()


# Thread to allow GUI and sockets to work together
class Server_Thread(threading.Thread):

    def __init__(self, host, port, gui):
        threading.Thread.__init__(self)
        self.server = ConnectionHandler(host, port, gui)

    def run(self):
        try:
            asyncore.loop()
        except:
            return 0

    def stop(self):
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
        self.menuListen = self.widget.findChild(QAction, "menuListen")
        self.menuQuit = self.widget.findChild(QAction, "menuQuit")
            # Text Edit
        self.teActivity = self.widget.findChild(QTextEdit, "teActivity")
            # Buttons
        self.pbListen = self.widget.findChild(QPushButton, "pbListen")
        self.pbExit = self.widget.findChild(QPushButton, "pbExit")
        # Connect Objects to Functions
            # Buttons
        self.pbListen.clicked.connect(self.Start_Server)
        self.pbExit.clicked.connect(self.ExitApp)
            # Menu Items
        self.menuListen.triggered.connect(self.Start_Server)
        self.menuQuit.triggered.connect(self.ExitApp)

        # Launch Application
        self.app.exec_()

    # Exit App
    def ExitApp(self):
        self.server.server.close()
        self.server.join()
        sys.exit(0)

    # Start the server thread
    def Start_Server(self):
        self.server = Server_Thread("localhost", 8192, self)
        self.server.start()

    # Write <data> to the GUI chat log element
    def Write_Log(self, data):
        self.teActivity.append(data)

ChatServerGUI()
