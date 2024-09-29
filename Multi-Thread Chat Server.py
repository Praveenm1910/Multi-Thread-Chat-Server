import socket as s
from threading import Thread
from time import sleep

# Goals
"""
1. It has to be multi-threaded.
2. It has to be a group chat.
3. One message has to be delivered to all the connected clients.
4. The server has to take the user's name and announce when a person joins or leaves.
5. Message length: 1024 bytes.
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
            sleep(0.25)
            if len(self.messages) > 0:
                for data in self.messages:
                    user = data[0]
                    msg = data[1]
                    for thread in self.threads:
                        if thread.getUsername() != user:
                            print("[bot_send_message] {}: {}".format(user, msg))
                            thread.sendMessage(f"\n{user}: {msg}")
                self.messages.clear()


class ChatServerOutgoingThread(Thread):
    def __init__(self, incoming_thread):
        Thread.__init__(self)
        self.incoming_thread = incoming_thread
        self.messages = []
        self.can_kill = False

    def sendMessage(self, message):
        try:
            conn = self.incoming_thread.getConnection()
            conn.sendall(message.encode())
        except:
            bot.removeChatThread(self.incoming_thread)
            self.killThread()

    def queueMessage(self, message):
        self.messages.append(message)
        print(f"[queue_message] {message}")

    def killThread(self, should_inform=False):
        if should_inform:
            bot.queueMessages("Server Bot", f"{self.incoming_thread.getUsername()} has left the chat.\n")
        self.can_kill = True

    def run(self):
        while True:
            sleep(0.1)
            if self.can_kill:
                break
            if len(self.messages) > 0:
                message = self.messages.pop(0)
                try:
                    print(f"[send_message] {message}")
                    self.sendMessage(message)
                except:
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

    def initSendMessageThread(self):
        self.outgoing_thread = ChatServerOutgoingThread(self)
        self.outgoing_thread.start()

    def sendMessage(self, message):
        self.outgoing_thread.queueMessage(message)

    def killThread(self):
        bot.removeChatThread(self)
        self.conn.close()
        self.can_kill = True

    def run(self):
        self.initSendMessageThread()
        sleep(0.2)
        self.sendMessage("\nWelcome to the Group Chat Server!\n")
        self.sendMessage(f"\nYou are connected from {self.user_ip}:{self.user_port} \n")
        self.sendMessage("\nPlease enter your name: \n")

        data = self.conn.recv(1024).decode().strip()
        if not data:
            self.killThread()
            return

        self.setUsername(data)
        bot.queueMessages("Server Bot", f"{self.username} has joined the chat.\n")
        self.sendMessage(f"\nWelcome, {self.username}! You can now chat with the group...\n")

        while True:
            try:
                data = self.conn.recv(1024).decode().strip()
                if not data:
                # Means, the client has disconnected
                # Inform others that the client has disconnected.
                    self.killThread()
                    break
                print(f"{self.username}: {data}")
                if data.lower() == "exit":
                    bot.queueMessages("Server Bot", f"{self.username} has left the chat.\n")
                    self.killThread()
                    break
                else:
                    bot.queueMessages(self.username, data)
            except:
                self.killThread()
                break


HOST = ''
PORT = 7777

bot = ChatBotThread()
bot.start()

binding = (HOST, PORT)

sock = s.socket(s.AF_INET, s.SOCK_STREAM) # AF_INET means Domain name or IPv4 Address and SOck_STREAM means TCP communication
sock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, True)
sock.bind(binding)
sock.listen()

print(f"Server started on {HOST}:{PORT}")

while True:
    try:
        conn, addr = sock.accept()
        t = ChatServerIncomingThread(conn, addr)
        t.start()
        bot.addChatThread(t)
    except KeyboardInterrupt:
        print("Server shutting down...\n")
        sock.close()
        break
