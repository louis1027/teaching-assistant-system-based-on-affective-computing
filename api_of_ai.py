from utils import Message
import random


def ai_api(msg: Message):
    '''ai 接口分析用户的情感得出是 -1 消极 0一般 +1 积极'''
    return random.choice([-1, 0, 1])


def ai_mood(mood):
    '''ai 根据学生的情感得分-1，0， +1 来获取自动应答的信息'''
    data = {
        '-1': ['Chill up, if you have any question, ask me after class without hesitate!'],
        '0': ['good day', 'good weather'],
        '1': ['Good job, keep this way']
    }
    return random.choice(data[str(mood)])
