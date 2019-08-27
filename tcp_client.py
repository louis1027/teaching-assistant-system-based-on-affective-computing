import socket
import threading
from queue import Queue, PriorityQueue
from utils import Message, localtime
from notices import *
import time


host = '127.0.0.1'
port = 5001


class ChatClient:

    def __init__(self, occupation='student'):
        self.username = 'Client'
        self.occupation = occupation
        self.token = None
        self.conn = None
        self.msgs = []
        self.q = PriorityQueue()
        self.friends = {}

        self.online = False
        self.flag = True
        self.hook = None

    def run(self):

        if not self.online:
            print('NotInLogin')
            return
        t1 = threading.Thread(target=self.receive)
        t2 = threading.Thread(target=self.send)
        t3 = threading.Thread(target=self.heart_beat)
        t1.setDaemon(True)
        t2.setDaemon(True)
        t3.setDaemon(True)
        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()


    def close(self):
        self.flag = False

    def get_all_users(self):
        if not self.online:
            return False
        msg = Message(
            kind=kind_get_all_users,
            sender=self.username,
            receiver='',
        )
        self.q.put_nowait((2, msg))
        return True

    def p2p_chat(self, receiver, info):
        '''chat one to one'''
        if not self.online:
            return False
        msg = Message(
            kind=kind_p2p_chat,
            sender=self.username,
            receiver=receiver,
            info=info,
            token=self.token)
        self.q.put_nowait((1, msg))
        return True

    def emotion(self, receiver='', info=''):
        '''student send emotion, teacher reply to emotion'''
        msg = Message(
            kind=kind_emotion,
            sender=self.username,
            receiver=receiver,
            info=info,
            token=self.token
        )
        print('emotion', msg)
        self.q.put_nowait((1, msg))
        return True

    def register(self):
        '''init connection and login a exist user'''
        if not isinstance(self.conn, socket.socket):
            return False, 'Not Connected to server'.title()
        conn = self.conn
        msg = Message(kind=kind_register, sender=self.username, receiver='')
        try:
            conn.sendall(msg.inBytes)
        except socket.error:
            print('{}, RegisterError, can not send RegisterReq to server'.format(localtime()))
            return False, 'RegisterError, can not send RegisterReq to server'
        data = conn.recv(1024)
        try:
            msg = Message.ParseBytes(data)
        except:
            print('{}, RegisterError, failed to parse server response'.format(localtime()))
            return False, 'RegisterError, failed to parse server response'
        print(msg)
        if msg.kind == kind_register and msg.token and isinstance(msg.token, str) and msg.info == 'ok':
            print('{}, RegisterAndLoginSuccess, token is {}'.format(localtime(), msg.token))
            self.token = msg.token
            self.online = True
            self.conn = conn, 'RegisterAndLoginSuccess'
            return True

        self.conn = None
        self.token = None
        conn.close()
        return False, 'Register Failed'

    def login(self):
        if not isinstance(self.conn, socket.socket):
            return False, 'Not Connected to server'.title()
        conn = self.conn
        # send to server username
        msg = Message(kind=kind_login, sender=self.username, receiver='')
        try:
            conn.sendall(msg.inBytes)
        except socket.error:
            print('{}, LoginError, can not send LoginReq to server'.format(localtime()))
            return False, 'LoginError, can not send LoginReq to server'

        # receive server response to login req
        data = conn.recv(1024)
        # print('receive server response to login req', data)
        try:
            msg = Message.ParseBytes(data)
        except:
            print('{}, LoginError, failed to parse server response'.format(localtime()))
            print(str(data, encoding='utf-8'))
            return False, 'LoginError, failed to parse server response'
        print(msg)
        if msg.kind in [kind_login, kind_register] and msg.token and isinstance(msg.token, str) and msg.info == 'ok':
            print('{}, LoginSuccess, token is {}'.format(localtime(), msg.token))
            self.token = msg.token
            self.online = True
            self.conn = conn
            return True, 'LoginSuccess'

        self.conn = None
        self.token = None
        conn.close()
        return False, msg.info

    def re_login_with_token(self):
        if self.online is False and self.token:
            if self.conn is not None:
                self.init_connect()
            conn = self.conn
            msg = Message(kind=kind_relogin, sender=self.username, receiver='', token=self.token)
            try:
                conn.sendall(msg.inBytes)
            except socket.error:
                print('{}, ReLoginError, can not send ReLoginReq to server'.format(localtime()))
                return False
            self.conn = conn
            return True
        return False

    def receive(self):
        while self.flag:
            if self.token is None or self.conn is None:
                continue
            try:
                data = self.conn.recv(1024)
            except socket.error:
                continue
            try:
                msg = Message.ParseBytes(data)
            except (TypeError, ValueError):
                continue
            if msg.kind == kind_relogin and msg.info == info_ok:
                print('{}, ReLogin success!'.format(localtime()))
                self.online = True

            if msg.kind == kind_heartbeat and msg.info == info_ok:
                print('{}, HeartBeat from server'.format(localtime()))

            if msg.kind == kind_get_all_users:
                self.friends.update(msg.info)

            if msg.kind == kind_emotion:
                self.store_new_messages(msg)

    def heart_beat(self):
        '''send heart beat package every 5 s'''
        while self.flag:
            if self.conn is None:
                print('{}, NoConnection, heartbeat skip.'.format(localtime()))
                continue
            if self.token is None:
                print('{}, NoToken, heartbeat skip.'.format(localtime()))
            msg = Message(kind=kind_heartbeat, sender=self.username, receiver='', token=self.token)
            try:
                self.q.put_nowait((8, msg))
            except socket.error:
                self.online = False
            time.sleep(5)

    def send(self):
        '''send msg in the queue one by one'''
        while self.flag:
            if self.token is None or self.conn is None or self.online is False:
                continue
            if self.q.empty():
                continue
            if not self.online:
                self.re_login_with_token()  # send re login request
                continue
            _, msg = self.q.get()
            print(_, msg)
            print(msg.kind)
            if msg.kind == kind_emotion:
                self.store_new_messages(msg)
            try:
                self.conn.sendall(msg.inBytes)
            except socket.error:
                print('{}, FailedToSendMsg: {},{}, {}'.format(
                    localtime(), msg.kind, msg.info, localtime(msg.timestamp))
                )
                pass

    def init_connect(self):
        conn = socket.socket()
        try:
            conn.connect((host, port), )
        except socket.error:
            print('{}, ConnectionError, can not connect to server'.format(localtime()))
            return False, 'ConnectionError, can not connect to server'
        data = conn.recv(1024)
        try:
            msg = Message.ParseBytes(data)
        except:
            print('{}, RegisterError, failed to parse server response'.format(localtime()))
            return False, 'RegisterError, failed to parse server response'
        print(msg)
        self.conn = conn
        return True, 'Connected'

    def store_new_messages(self, msg):
        self.msgs.append(msg)
        if self.hook is not None:
            self.hook(msg)

    def quit(self):
        print('tcp client quit')
        self.flag = False


if __name__ == '__main__':
    c = ChatClient()

    c.username = 'lk'
    c.init_connect()
    print(c.login())
    c.run()

