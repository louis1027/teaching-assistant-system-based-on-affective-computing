import uuid
import json
import socket
import time


def localtime(timestamp=0):
    if timestamp:
        return time.strftime('%X', time.localtime(timestamp))
    return time.strftime('%X', time.localtime())


def id_generate(history_id_db=None):
    db = set()
    if isinstance(history_id_db, (list, set, tuple)):
        db.update(set(history_id_db))
    while True:
        _id = str(uuid.uuid4())
        if _id not in db:
            yield _id
            db.add(_id)


id_gen = id_generate()


class Message:
    def __init__(self, kind, sender, receiver, info='', status='', token='', timestamp=0):

        '''
        {
            'from': sender,
            'to': receiver,
            'kind': str,
            'info': str or dict,
            'room_id': str,
            'status': ok,  -- not used for now
            'token' : token,
        }

        '''

        self.check_valid(locals())

        self.kind = kind
        self.sender = sender
        self.receiver = receiver
        self.info = info
        self.status = status
        self.token = token
        if timestamp == 0:
            self.timestamp = time.time()
        else:
            self.timestamp = float(timestamp)

    @classmethod
    def ParseBytes(cls, messge_bytes):
        if not isinstance(messge_bytes, bytes):
            raise TypeError

        message = str(messge_bytes, encoding='utf-8')

        try:
            message = json.loads(message)
        except json.JSONDecodeError:
            raise

        return cls(**message)

    @property
    def inBytes(self):
        return bytes(
            json.dumps({
                'kind': self.kind,
                'sender': self.sender,
                'receiver': self.receiver,
                'info': self.info,
                'status': self.status,
                'token': self.token,
                'timestamp': self.timestamp,
            }), encoding='utf-8'
        )

    @classmethod
    def check_valid(cls, message_data):
        if not isinstance(message_data, dict):
            raise TypeError
        for k in ['kind', 'sender', 'receiver', 'info', 'status', 'timestamp']:
            if k == 'timestamp':
                if not isinstance(message_data[k], (int, float)):
                    raise TypeError
                continue
            if k not in message_data:
                raise ValueError
            if k == 'receiver':
                if not isinstance(message_data[k], str):
                    raise TypeError
                continue
            if k == 'info':
                if not isinstance(message_data[k], (str, dict)):
                    raise TypeError
                continue

            if not isinstance(message_data[k], str):
                raise ValueError
        # todo check more data
        kind = message_data['kind']
        info = message_data['info']

    def __str__(self):
        return str(self.inBytes, encoding='utf-8')

    def __repr__(self):
        return '[Message: {},{},{}]'.format(self.timestamp, self.sender, self.receiver)

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError
        if other.timestamp > self.timestamp:
            return True
        else:
            return False

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError
        if other.timestamp > self.timestamp:
            return False
        else:
            return True


class User:

    def __init__(self, username, occupation='student'):
        self.username = username
        self.occupation = occupation
        self.token = None
        self.conn = None

    def __eq__(self, other):
        if not isinstance(other, User):
            raise TypeError
        if self.token is not None:
            return self.token == other.token
        if self.conn is not None:
            return self.conn == other.conn
        return self.username == other.username

    def login(self, conn):
        self.conn = conn
        self.token = next(id_gen)

    def logout(self):
        try:
            if isinstance(self.conn, socket.socket):
                self.conn.close()
        except socket.error:
            pass
        finally:
            self.conn = None
        self.token = None

    def __str__(self):
        return self.username

    def __repr__(self):
        return '<User: {}>'.format(self.username)


