import socket as s
from threading import Thread
from time import sleep

#Goals

"""
!. It has to be multi threaded
2. It has to be a group chat
3. One message has to be delivered to all the connected cliets
4. The server has to take the user's name and tell when a person leaves.
5. Message lenght: 1024 
"""


class ChatBotThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.threads = []
        self.messages = []

    def addChatThread(self, thread):
        self.threads.append(thread)

    def removeChatThread(self, thread):
        if thread in self.threads:
            self.threads.remove(thread)

    def queueMessages(self, user, message):
        data = (user, message)
        self.messages.append(data)
        print("[bot_queue_message] {}: {}".format(user, message))

    def run(self):
        while True:
            sleep(0.25) #25ms
            if len(self.messages) > 0:
                for thread in self.threads:
                    for data in self.messages:
                        user = data[0]
                        msg = data[1]
                        if thread.getUsername() != user:
                            print("[bot_send_message] {}: {}".format(user, msg))
                            thread.sendMessage(msg)

class ChatServerOutgoingThread(Thread):
    def __init__(self, incomming_thread):
        Thread.__init__(self)
        self.incoming_thread = incomming_thread
        self.messages = []
        self.can_kill = False

    def sendMessage(self, user, message):
        fMessage = "{username}: {message}".format(username = user, message = message)
        try:
            conn = self.incoming_thread.getConnection()
            conn.sendall(fMessage.encode())
            conn.flush()
        except:
            bot.removeChatThread(self.incoming_thread)
            self.killThread()

    def queueMessage(self, user, message):
        data = (user, message)
        self.messages.append(message)
        print("[queue_message] {}: {}".format(user, message))

    def killThread(self, should_inform = False):
        # Inform others that this user has disconnected
        self.can_kill = True

    def run(self):
        while True:
            sleep(0.1) # 100 milliseconds
            if self.can_kill:
                break # If this loop breaks, then the thread has to end.
            if len(self.messages) > 0:
                for message in self.messages:
                    try:
                        print("[Send_message] {}: {}".format(message[0], message[1]))
                        self.sendMessage(message[0], message[1])
                    except:
                        # Inform others that the client has disconnected.
                        break


class ChatServerIncomingThread(Thread):
    def __init__(self, conn, addr):
        Thread.__init__(self)
        self.conn = conn
        self.addr = addr 
        self.username = ""
        self.user_ip = addr[0]
        self.user_port = addr[1]
        self.outgoing_thread = None
        self.can_kill = False

    def setUsername(self, username):
        self.username = username

    def getUsername(self):
        return self.username
    
    def getConnection(self):
        return self.conn

    def isClosed(self):
        return self.conn._closed
    
    def initSendMessageThread(self):
        self.outgoing_thread = ChatServerOutgoingThread(self)
        self.outgoing_thread.start()

    def sendMessage(self, message):
        self.outgoing_thread.queueMessage(self.getUsername(), message)
    
    def broadcastMessage(self, message):
        self.outgoing_thread.queueMessage("Server Bot", message)

    def killThread(self):
        bot.removeChatThread(self)
        self.can_kill = True     

    def run(self):
        self.initSendMessageThread()
        sleep(0.2)
        self.broadcastMessage("Welcome to my Group Chat Server...\n\n")
        self.broadcastMessage("You are connected from {}:{} \n".format(self.user_ip, self.user_port))
        self.broadcastMessage("Please enter your name to continue: ")
        data = self.conn.recv(1024)
        if not data: 
                self.outgoing_thread.killThread()
                self.killThread()
                return
        else:
            self.setUsername(data.decode()) 
        self.broadcastMessage("You can now chat with our group....\n\n")     
        while not self.conn._closed:
            data = self.conn.recv(1024)
            if not data: # Means, the client has disconnected
                # Inform others that the client has disconnected.
                self.outgoing_thread.killThread()
                self.killThread()
                break
            if data.decode().strip() == "kill":
                self.killThread()
            else:
                print("{ip}: {message}".format(ip=self.getUsername(), message=data.decode()))
                bot.queueMessages(self.getUsername(), data.decode().strip())

HOST = ''
PORT = 5555

bot = ChatBotThread()
bot.start()

binding = (HOST, PORT)

sock = s.socket(s.AF_INET, s.SOCK_STREAM) # AF_INET means Domain name or IPv4 Address and SOck_STREAM means TCP communication
sock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, True)
sock.bind(binding)
sock.listen()
while not sock._closed:
    conn, addr = sock.accept()
    t = ChatServerIncomingThread(conn, addr)
    t.start()
    bot.addChatThread(t)

if not sock._closed():
    sock.close()

 
