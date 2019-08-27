import threading
import socketserver
import socket
import json
import time
import uuid

from utils import Message, User, localtime
from notices import *
from api_of_ai import ai_api

host = '0.0.0.0'
port = 5001

conn_user_map = {}
token_user_map = {}
users = {
    'teacher': User(username='teacher', occupation='teacher'),  # 默认新建一个 teacher

}

emotions = []

running = True


class ChatSever(socketserver.BaseRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self):

        c = self.request
        print(localtime(), c)
        try:
            message = Message(kind=server_ask_username, sender=server_name, receiver='', info=welcome_msg)
            c.sendall(message.inBytes)
        except:
            c.close()
            return
        try:
            data = c.recv(1024)
        except:
            c.close()
            return
        try:
            message = Message.ParseBytes(data)
        except:
            self.__send_data_close(c, invalid_msg)
            return

        # print(message, users)

        user_name = message.sender

        # print('check', message.kind)

        # 处理用户登陆
        if message.kind == 'Login':
            self.login(c, user_name)

        # 处理用户注册
        elif message.kind == kind_register:
            self.register(c, user_name)

        # 处理已登陆用户重联 --- 用户不稳定的网络
        elif message.kind == kind_relogin:
            result = self.re_login_with_token(c, message.sender, message.token)
            if result is not True:
                self.__send_data_close(c, invalid_token)
                return
            else:
                if not self.__send_data(conn=c, info='ok', kind=kind_relogin):
                    c.close()
                    return
        else:
            self.__send_data_close(c, invalid_msg)
            return

        while True:
            if running is not True:
                break
            try:
                data = c.recv(1024)
            except:
                self.logout(user_name)
                break
            try:
                message = Message.ParseBytes(data)
            except:
                continue

            sender = message.sender
            info = message.info
            receiver = message.receiver
            kind = message.kind
            status = message.status
            token = message.token

            if token is None:
                self.__send_data_close(c, invalid_token)
                break

            if token not in token_user_map:
                self.__send_data_close(c, invalid_token)
                break

            # 心跳
            if kind == kind_heartbeat:
                if token in token_user_map \
                        and token_user_map[token].token == token \
                        and sender == token_user_map[token].username:
                    self.__send_data(c, 'ok', 'HeartBeat')
                else:
                    self.__send_data_close(c, invalid_token)
                    break

            # 用户登出
            if kind == kind_exit:
                self.logout(user_name)
                break

            # 获取用户列表和用户状态
            if kind == kind_get_all_users:
                self.__send_data(conn=c, info=json.dumps(self.users_status_batch), kind=kind)
                continue

            # 获取某个用户的状态
            if kind == kind_get_user_status:
                self.__send_data(c, self.check_user(info), kind)
                continue

            # p2p chat
            if kind == kind_p2p_chat:
                receiver = users[receiver]
                self.__send_data(receiver.conn, info=info, kind=kind)  # todo: the partner offline

            ###############################################################
            # 用户情绪
            ###############################################################
            if kind == kind_emotion:

                # emotions.append(message)
                sender_ = users[sender]
                if sender_.occupation == 'student':

                    teacher = users['teacher']
                    self.__send_data(
                        teacher.conn,
                        info={
                            'talk': message.info,
                            'mood': ai_api(message)
                            # 利用ai把学生的发言分析成-1，0， +1中的一个，并发送给教师端
                        },
                        kind=kind_emotion,
                        sender=sender
                    )
                    print(teacher, teacher.conn,)
                elif sender_.occupation == 'teacher':
                    if not receiver:
                        continue
                    student = users[receiver]
                    self.__send_data(
                        student.conn,
                        info=message.info,
                        kind=kind_emotion,
                        sender=sender

                    )


    def register(self, conn, user_name):
        '''register new user, and  login the user'''
        if user_name in users:
            self.__send_data_close(conn, usr_exist)
            return False

        user = User(username=user_name)
        user.login(conn)

        users[user_name] = user
        conn_user_map[conn] = user
        token_user_map[user.token] = user
        self.__send_data(conn=conn, info=info_ok, kind=kind_register, token=user.token)

        return True

    def login(self, conn, user_name):
        '''登陆用户'''
        if user_name not in users:
            return self.register(conn, user_name)
        user = users[user_name]

        if user.token is None:
            # login the user
            if user.conn in conn_user_map:
                conn_user_map.pop(user.conn)
            user.logout()
            user.login(conn)
            conn_user_map[conn] = user
            token_user_map[user.token] = user
            return self.__send_data(conn=conn, info='ok', kind='Login', token=user.token)
        else:
            return self.__send_data(conn=conn, info=info_ok, kind=kind_login, token=user.token)

    def re_login_with_token(self, conn, user_name, token):
        if token and token in token_user_map and user_name and user_name in users:
            t_user = token_user_map[token]
            u_user = users[user_name]
            if u_user.username != t_user.username or t_user.token != u_user.token:
                return invalid_token
            if u_user.conn in conn_user_map:
                try:
                    u_user.conn.close()
                except:
                    pass
                conn_user_map.pop(u_user.conn)
                u_user.conn = conn
            conn_user_map[conn] = u_user
            return True
        else:
            return invalid_token

    def update_user_conn(self, user_token, conn):
        pass

    def logout(self, user_name):
        '''登出用户，关闭连接，并广播消息'''
        if user_name not in users:
            return
        user = users[user_name]
        if user.conn in conn_user_map:
            conn_user_map.pop(user.conn)
        if user.token in token_user_map:
            token_user_map.pop(user.token)

        user.logout()

        self.broadcast('Logout {}'.format(user_name))

    def p2p_chat(self, sender, receiver, info, kind='p2p_chat'):
        '''点对点聊天'''
        if self.check_user(receiver) != usr_online:
            return False
        receiver = users[receiver]
        conn = receiver.conn
        message = Message(kind=kind, sender=sender, receiver='', info=info)
        try:
            conn.sendall(message.inBytes)
            return True
        except:
            self.logout(receiver)
            return False

    def broadcast(self, info):
        '''广播消息'''
        message = Message(kind='BroadCasting', sender=server_name, receiver='', info=info)
        for conn in conn_user_map:
            try:
                receiver = conn_user_map[conn]
                conn.sendall(message.inBytes)
            except:
                if 'receiver' in locals():
                    receiver = locals()['receiver']
                    self.logout(user_name=receiver.username)

    def check_user(self, user_name):
        '''检查用户状态'''
        if user_name not in users:
            return usr_not_exist
        user = users[user_name]
        if user.token not in token_user_map or user.conn not in conn_user_map:
            return usr_offline
        return usr_online

    def check_data(self, message):
        '''检查消息实例'''
        if not isinstance(message, Message):
            return False
        return True

    def __send_data_close(self, conn, info):
        '''服务器发送警告消息后关闭连接'''
        message = Message(kind="server_will_close", sender=server_name, receiver='', info=info)
        try:
            conn.sendall(message.inBytes)
        except:
            pass
        finally:
            conn.close()

    def __send_data(self, conn, info, kind, token='', sender=None):
        '''服务器发送信息给用户'''
        message = Message(kind=kind, sender=server_name if sender is None else sender, receiver='', info=info, token=token)
        try:
            conn.sendall(message.inBytes)
            return True
        except:
            return False

    @property
    def users_status_batch(self):
        result = {}
        for user_name, user in users.items():
            if user.conn in conn_user_map:
                result[user_name] = True
            else:
                result[user_name] = False
        return result

    def __close_conn(self, conn):
        if not isinstance(conn, socket.socket):
            return
        if conn in conn_user_map:
            user = conn_user_map[conn]
            user.logout()
        else:
            conn.close()



if __name__ == '__main__':
    # 创建一个多线程TCP服务器
    server = socketserver.ThreadingTCPServer((host, port), ChatSever)
    print("ChatServer@{}:{} ".format(host, port))
    # 启动服务器，服务器将一直保持运行状态
    try:
        server.serve_forever()
    except (KeyboardInterrupt, OSError):
        running = False
        server.shutdown()



