import tkinter as tk
import tkinter.ttk
import tkinter.messagebox
import sys
from functools import partial
import socket
from utils import Message
from tcp_client import ChatClient
from notices import *
from PIL import ImageTk, Image
import os
import threading

from api_of_ai import ai_mood

img_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'img')
APP_TITLE = 'Education App'
bg_color = 'white'
bg_color_ls = ('white', 'yellow', 'green', 'blue', 'brown')
host = '127.0.0.1'
port = 5002

icon_size = (48, 48)


def load_image(img_path, size=icon_size):
    if not os.path.exists(img_path):
        raise FileNotFoundError
    if not isinstance(size, tuple):
        raise TypeError

    img = Image.open(img_path)

    return ImageTk.PhotoImage(image=img.resize(size))


def resize_image(img, size):
    if not isinstance(img, Image.Image):
        raise TypeError
    return ImageTk.PhotoImage(image=img.resize(size))


global chat_client


emoji_dict = {
    '-1': os.path.join(img_dir, 'Sleeping_with_Snoring_Emoji_large.png'),
    '0': os.path.join(img_dir, 'Slightly_Smiling_Face_Emoji_large.png'),
    '1': os.path.join(img_dir, 'Smiling_Face_Emoji_large.png')
}


class AbstractFunc(object):
    def update_color(self, color=None):
        global bg_color

        if color in bg_color_ls and color != bg_color:
            bg_color = color
        elif color is None:
            if 'bg_color' in self.__dict__:
                self.bg_color = bg_color

            if 'friends' in self.__dict__:
                for friend in self.__dict__['friends']:
                    try:
                        self.__dict__['friends'][friend].update_color()
                        self.__dict__['friends'][friend].config(bg=bg_color)
                    except:
                        pass
            pass
        else:
            return

        print('update_color')
        for k in self.__dict__:
            if isinstance(self.__dict__[k],
                          (tk.Frame, tk.Label, tk.Listbox, tk.Button, tk.Text, tk.Entry, tk.LabelFrame)):
                self.__dict__[k].config(bg=bg_color)

        try:
            self.master.update_color()
        except:
            pass


class MainApp(tk.Tk, AbstractFunc):
    '''主窗类'''

    def __init__(self):
        global chat_client
        super().__init__()
        self.title(APP_TITLE)

        self.host_var = tk.StringVar(value=host)
        self.port_var = tk.IntVar(value=port)

        self.bg_color = bg_color

        window_height = 720
        window_width = 320
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (window_width / 2))
        y_coordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry("{}x{}+{}+{}".format(window_width, window_height, x_coordinate, y_coordinate))
        self.minsize(width=window_width, height=window_height)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.main_frame = tk.Frame(self, bg=self.bg_color)  # color
        self.main_frame.grid(row=0, column=0, sticky='nsew', )
        self.main_frame.columnconfigure(0, weight=1)

        # menu bar
        self.main_frame.rowconfigure(0, weight=1)
        self.menu_area = tk.Frame(self.main_frame, bg=self.bg_color)  # color
        self.menu_area.grid(row=0, column=0, sticky='nwe', padx=5)

        self.menu_area.columnconfigure(0, weight=1)
        self.menu_area.columnconfigure(1, weight=1)
        self.menu_area.columnconfigure(2, weight=1)
        self.menu_area.rowconfigure(0, weight=1)

        self.config_btn = tk.Button(
            master=self.menu_area,
            text='Config',
            command=self.show_config,
            bg=self.bg_color,

        )
        self.config_btn.grid(row=0, column=0, padx=6, sticky='nsew')
        self.help_btn = tk.Button(
            master=self.menu_area,
            text='Help',
            command=self.show_help,
            bg=self.bg_color,
        )
        self.help_btn.grid(row=0, column=1, padx=6, sticky='nsew')
        self.exit_btn = tk.Button(
            master=self.menu_area,
            text='Exit',
            command=self.show_exit,
            bg=self.bg_color,
        )
        self.exit_btn.grid(row=0, column=2, padx=6, sticky='nsew')

        # user name
        self.main_frame.rowconfigure(1, weight=1)
        self.name_label = tk.Label(
            self.main_frame,
            text='Dear {}, Welcome!'.format(chat_client.username),
            bg=self.bg_color)
        self.name_label.grid(
            row=1, column=0, pady=10, sticky='new'
        )

        # send emotion
        self.main_frame.rowconfigure(2, weight=1)
        self.groups_frame = tk.LabelFrame(
            self.main_frame,
            bg=bg_color,
            text='Send Emotion' if chat_client.occupation == 'student' else 'View Students')
        self.groups_frame.grid(row=2, column=0, sticky='new')
        self.group_talk_btn = tk.Button(
            self.groups_frame,
            text='Check In' if chat_client.occupation == 'student' else 'Open',
            command=self.emotion_talk
        )
        self.group_talk_btn.pack()

        self.__t = threading.Thread(target=chat_client.run)
        self.__t.setDaemon(True)
        self.__t.start()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def show_config(self):
        self.config_btn.config(state=tk.DISABLED)
        config_window = ConfigWindow(self)
        config_window.port_entry.config(state=tk.DISABLED)
        config_window.ip_entry.config(state=tk.DISABLED)
        self.wait_window(config_window)
        self.config_btn.config(state=tk.NORMAL)

    def show_help(self):
        print('help')
        self.help_btn.config(state=tk.DISABLED)
        config_page = HelpPage(self)
        self.wait_window(config_page)
        self.help_btn.config(state=tk.NORMAL)

    def show_exit(self):
        self.destroy()

    def emotion_talk(self):
        self.group_talk_btn.config(state=tk.DISABLED)
        chat_window = TalkWindow(self, kind=kind_emotion)
        self.wait_window(chat_window)
        try:
            self.group_talk_btn.config(state=tk.NORMAL)
        except tk.TclError:
            pass

    def on_close(self):
        chat_client.quit()
        self.__t.join()


class ConfigWindow(tk.Toplevel, AbstractFunc):
    '''设置面板'''

    def __init__(self, master):
        super().__init__(master, bg=master.bg_color)

        window_height = 320
        window_width = 480
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (window_width / 2))
        y_coordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry("{}x{}+{}+{}".format(window_width, window_height, x_coordinate, y_coordinate))
        self.minsize(width=window_width, height=window_height)
        self.resizable(False, False)

        self.title('{} Help'.format(APP_TITLE))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.main_frame = tk.Frame(self, bg=self.master.bg_color)
        self.main_frame.grid(row=0, column=0, sticky='news')

        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=2)
        self.main_frame.rowconfigure(2, weight=1)
        self.main_frame.rowconfigure(3, weight=1)
        self.main_frame.rowconfigure(4, weight=1)

        # header area
        self.header_area = tk.Frame(self.main_frame, bg=self.master.bg_color)
        self.header_area.grid(row=0, column=0, sticky='news', pady=20)

        self.header_area.columnconfigure(0, weight=1)
        self.header_area.rowconfigure(0, weight=1)

        self.header_label = tk.Label(
            self.header_area,
            text='{} Config'.format(APP_TITLE),
            justify='center',
            bg=self.master.bg_color,
        )
        self.header_label.grid(row=0, column=0, sticky='news')

        # input area
        self.input_area = tk.Frame(self.main_frame, bg=self.master.bg_color)
        self.input_area.grid(row=1, column=0, sticky='news', padx=30)
        self.input_area.columnconfigure(0, weight=1)
        self.input_area.columnconfigure(1, weight=5)
        self.input_area.rowconfigure(0, weight=1)
        self.input_area.rowconfigure(1, weight=1)

        self.ip_label = tk.Label(
            self.input_area,
            text='Host:',
            bg=self.master.bg_color
        )
        self.ip_label.grid(row=0, column=0, sticky='new')

        self.ip_entry = tk.Entry(self.input_area, textvariable=self.master.host_var)
        self.ip_entry.grid(row=0, column=1, sticky='new')

        self.port_label = tk.Label(
            self.input_area,
            text='Port:',
            bg=self.master.bg_color,
        )
        self.port_label.grid(row=1, column=0, sticky='new')
        self.port_entry = tk.Entry(self.input_area, textvariable=self.master.port_var)
        self.port_entry.grid(row=1, column=1, sticky='new')

        # color setup
        self.color_area = tk.Frame(self.main_frame, bg=self.master.bg_color)
        self.color_area.grid(row=2, column=0, sticky='news', padx=30)

        self.color_area.columnconfigure(0, weight=1)
        self.color_area.columnconfigure(1, weight=1)
        self.color_area.columnconfigure(2, weight=1)
        self.color_area.columnconfigure(3, weight=1)
        self.color_area.columnconfigure(4, weight=1)
        self.color_area.columnconfigure(5, weight=1)

        self.color_area.rowconfigure(0, weight=1)

        self.color_label = tk.Label(
            self.color_area,
            text='Color:',
            bg=self.master.bg_color)
        self.color_label.grid(row=0, column=0, sticky='ew')

        for c, color in enumerate(bg_color_ls):
            self.color_area.columnconfigure(c + 1, weight=1)
            tk.Button(
                self.color_area,
                bg=color,
                command=partial(self.update_color, color),
            ).grid(
                row=0,
                column=c + 1,
                sticky='ew',
            )

        # btn area
        self.btn_area = tk.Frame(self.main_frame, bg=self.master.bg_color)
        self.btn_area.grid(row=3, column=0, sticky='news')
        self.btn_area.columnconfigure(0, weight=1)
        self.btn_area.columnconfigure(1, weight=1)
        self.btn_area.rowconfigure(0, weight=1)

        self.btn_cancel = tk.Button(self.btn_area, text='Cancel', command=self.destroy)
        self.btn_cancel.grid(row=0, column=0, sticky='e', padx=10)

        self.btn_confirm = tk.Button(self.btn_area, text='Confirm', command=self.do_config)
        self.btn_confirm.grid(row=0, column=1, sticky='w', padx=10)

        # hint area
        self.hint_area = tk.Frame(self.main_frame, bg=self.master.bg_color)
        self.hint_area.grid(row=4, column=0, sticky='news')
        self.hint_var = tk.StringVar(value='A little hint')
        self.hint_label = tk.Label(
            self.hint_area,
            bg=self.master.bg_color,
            textvariable=self.hint_var,
            justify='center',
            wraplength=200,
        )
        self.hint_label.pack(fill='x', expand=tk.YES)

    def do_config(self):
        print('config from config window')
        self.hint_var.set('')
        global host, port
        tmp_host = self.master.host_var.get()
        tmp_port = self.master.port_var.get()
        if tmp_port == port and tmp_host == host:
            self.destroy()
            return

        hint_msg = ''
        if not tmp_host:
            hint_msg += 'Host Can not be empty.'
            hint_msg += '\n'
        if not tmp_port:
            hint_msg += 'Port Can not be empty.'
            hint_msg += '\n'
        if tmp_port > 65535 or tmp_port < 0:
            hint_msg += 'Port is invalid, out of range or 0~65535.'
            hint_msg += '\n'
        else:
            conn = socket.socket()
            try:
                conn.connect((tmp_host, tmp_port))
                self.destroy()
            except socket.error:
                hint_msg += 'can not connected {}:{}'.format(tmp_host, tmp_port)
                hint_msg += '\n'
        self.hint_var.set(hint_msg)


class TalkWindow(tk.Toplevel):
    '''聊天窗口'''

    def __init__(self, master, kind, receiver=None):
        super().__init__(master, bg=master.bg_color)

        self._bg_color = master.bg_color

        window_height = 480
        window_width = 640
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (window_width / 2))
        y_coordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry("{}x{}+{}+{}".format(window_width, window_height, x_coordinate, y_coordinate))
        self.minsize(width=window_width, height=window_height)

        self.msgs = {}

        if kind == 'p2p_chat':
            self.title('Chatting with {} - {}'.format(receiver, APP_TITLE))
        if kind == 'group_chat':
            self.title('Group Chatting - {}'.format(APP_TITLE))
        if kind == kind_emotion:
            self.title('Show Emotion - {}'.format(APP_TITLE))

        self.kind = kind
        self.receiver = receiver

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.main_frame = tk.Frame(self, bg=bg_color)
        self.main_frame.grid(row=0, column=0, sticky='news')

        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=9)
        self.main_frame.rowconfigure(0, weight=1)

        if chat_client.occupation == 'student':
            self.chatting_frame = tk.LabelFrame(self.main_frame, bg=bg_color, text='Emotions')
        elif chat_client.occupation == 'teacher':
            self.chatting_frame = tk.LabelFrame(self.main_frame, bg=bg_color, text='Students')
        else:
            self.chatting_frame = tk.LabelFrame(self.main_frame, bg=bg_color, text='Chatting')
        self.chatting_frame.grid(row=0, column=0, sticky='news')
        self.chatting_frame.columnconfigure(0, weight=1)

        self.words_var = tk.StringVar()

        if chat_client.occupation == 'student':
            self.sending_frame = tk.Frame(self.main_frame, bg=bg_color)
            self.sending_frame.grid(row=1, column=0, sticky='news')

            self.sending_frame.columnconfigure(0, weight=8)
            self.sending_frame.columnconfigure(1, weight=1)

            self.sending_frame.rowconfigure(0, weight=1)


            self.words_entry = tk.Entry(self.sending_frame, textvariable=self.words_var, bg=self._bg_color)
            self.words_entry.grid(row=0, column=0, sticky='news')

            self.words_btn = tk.Button(self.sending_frame, bg=bg_color, text='Send', command=self.send_msg)
            self.words_btn.grid(row=0, column=1, sticky='nsew')

        chat_client.hook = self.show_msg
        # self.protocol("WM_DELETE_WINDOW", self.delete_hook)

    def send_msg(self):
        words = self.words_var.get()
        if not words:
            return
        self.words_var.set('')
        print(words)
        chat_client.emotion(receiver='', info=words)

    def show_msg(self, msg):
        if not isinstance(msg, Message):
            raise TypeError
        r = len(self.msgs)
        m = ShowMessage(master=self.chatting_frame, name=msg.sender, words=msg.info, time=msg.timestamp, kind=msg.kind)
        self.msgs[r+1] = m
        m.grid(row=r, column=0, sticky='new')

    def delete_hook(self):
        chat_client.hook = None


class ShowMessage(tk.Frame):
    '''聊天显示组件'''

    def __init__(self, master, name, words, time, kind):
        global chat_client
        super().__init__(master)
        if kind != kind_emotion:
            return
        self.bg_color = master.master.master._bg_color
        self.rowconfigure(0, weight=1)

        if chat_client.occupation == 'student':
            if name == chat_client.username:
                self.columnconfigure(0, weight=9)
                self.columnconfigure(1, weight=1)
                tk.Label(self, text=words, justify='left', anchor='e', bg=self.bg_color,
                         font=("arial", 12, 'bold', 'underline')
                         ).grid(row=0, column=0, sticky='news')
                tk.Label(self, text=name, justify='left', anchor='e', bg=self.bg_color
                         ).grid(row=0, column=1, sticky='news')

            else:
                self.columnconfigure(0, weight=1)
                self.columnconfigure(1, weight=9)

                tk.Label(self, text=name, justify='left', anchor='w', bg=self.bg_color
                         ).grid(row=0, column=0, sticky='news')

                tk.Label(self, text=words, justify='left', anchor='w', bg=self.bg_color,
                         font=("arial", 12, 'bold', 'underline'),
                         ).grid(row=0, column=1, sticky='news')

        elif chat_client.occupation == 'teacher':

            if name == chat_client.username:
                self.columnconfigure(0, weight=9)
                self.columnconfigure(1, weight=1)
                tk.Label(self, text=words, justify='left', anchor='e', bg=self.bg_color,
                         font=("arial", 12, 'bold', 'underline')
                         ).grid(row=0, column=0, sticky='news')
                tk.Label(self, text=name, justify='left', anchor='e', bg=self.bg_color
                         ).grid(row=0, column=1, sticky='news')

            else:
                # print(words)
                mood = words['mood']
                words = words['talk']


                self.emoji = load_image(emoji_dict[str(mood)])

                self.columnconfigure(0, weight=1)
                self.columnconfigure(1, weight=1)
                self.columnconfigure(2, weight=8)

                tk.Label(self, text=name, justify='left', anchor='w', bg=self.bg_color
                         ).grid(row=0, column=0, sticky='news')
                tk.Button(self, image=self.emoji, command=partial(self.send_msg, name, mood)
                          ).grid(row=0, column=1, sticky='news')

                tk.Label(self, text=words, justify='left', anchor='w', bg=self.bg_color,
                         font=("arial", 12, 'bold', 'underline'),
                         ).grid(row=0, column=2, sticky='news')

    def send_msg(self, name, mood):
        print(name)
        print('reply to student emotion')
        global chat_client
        chat_client.emotion(receiver=name, info=ai_mood(mood))


class HelpPage(tk.Toplevel):

    def __init__(self, master):
        super().__init__(master, bg=master.bg_color)

        window_height = 480
        window_width = 640
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (window_width / 2))
        y_coordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry("{}x{}+{}+{}".format(window_width, window_height, x_coordinate, y_coordinate))
        self.minsize(width=window_width, height=window_height)

        self.title('{} Help'.format(APP_TITLE))

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_frame = tk.Frame(self, bg=self.master.bg_color)
        self.main_frame.grid(row=0, column=0, sticky='news')
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=5)

        tk.Label(self.main_frame,
                 text='{} V0.1\nDeveloped by The Author'.format(APP_TITLE),
                 anchor='center',
                 pady=30,
                 bg=self.master.bg_color
                 ).grid(
            row=0, column=0, sticky='nswe', padx=10, )

        help_frame = tk.LabelFrame(self.main_frame, bg=self.master.bg_color, text='Details')
        help_frame.grid(row=1, column=0, sticky='news')
        help_frame.columnconfigure(0, weight=1)
        help_frame.rowconfigure(0, weight=1)
        scroll_help = tk.ttk.Scrollbar(help_frame)
        scroll_help.grid(row=0, column=1, sticky='ns')

        help_text = ' Help ' * 1028

        help_txt = tk.Text(help_frame, yscrollcommand=scroll_help.set, width=73, height=24, bg='black', fg='#99E335')

        help_txt.insert('1.0', help_text)

        scroll_help.config(command=help_txt.yview)
        help_txt.grid(row=0, column=0, ipadx=30, sticky='nswe')


class LoginWindow(tk.Tk, AbstractFunc):

    def __init__(self):
        super().__init__()
        self.title('Login {}'.format(APP_TITLE))

        self.bg_color = bg_color
        # init main window
        window_height = 360
        window_width = 480
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (window_width / 2))
        y_coordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry("{}x{}+{}+{}".format(window_width, window_height, x_coordinate, y_coordinate))
        self.resizable(False, False)

        self.host_var = tk.StringVar(value=host)
        self.port_var = tk.IntVar(value=port)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.main_frame = tk.Frame(self, bg=self.bg_color)  # color
        self.main_frame.grid(row=0, column=0, sticky='nsew', )

        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=2)
        self.main_frame.rowconfigure(1, weight=2)
        self.main_frame.rowconfigure(2, weight=1)
        self.main_frame.rowconfigure(3, weight=2)

        # header welcome
        self.header_area = tk.Frame(self.main_frame, bg=self.bg_color)
        self.header_area.grid(row=0, column=0, sticky='nswe', pady=15)
        self.header_area.columnconfigure(0, weight=1)
        self.header_area.rowconfigure(0, weight=1)
        self.welcome_label = tk.Label(
            self.header_area,
            text='Welcome to Use {}'.format(APP_TITLE),
            justify='center',
            bg=self.bg_color,
        )
        self.welcome_label.grid(row=0, column=0, sticky='news', pady=5)

        # user input
        self.user_input_area = tk.Frame(self.main_frame, bg=self.bg_color)
        self.user_input_area.grid(row=1, column=0, padx=20, sticky='news')

        self.user_input_area.columnconfigure(0, weight=1)
        self.user_input_area.columnconfigure(1, weight=5)

        self.user_input_area.rowconfigure(0, weight=1)
        self.user_input_area.rowconfigure(1, weight=1)

        self.username_label = tk.Label(
            self.user_input_area,
            text='UserName:',
            justify='left',
            bg=self.bg_color,
        )
        self.username_label.grid(row=0, column=0, pady=5, padx=5, sticky='e')

        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(
            self.user_input_area,
            textvariable=self.username_var,
            width=35,
        )
        self.username_entry.grid(row=0, column=1, pady=5, padx=5, sticky='w')

        self.password_label = tk.Label(
            self.user_input_area,
            text='Password:',
            justify='left',
            bg=self.bg_color,
        )
        self.password_label.grid(row=1, column=0, pady=5, padx=5, sticky='e')

        self.password_var = tk.StringVar(value='12345678')
        self.password_entry = tk.Entry(
            self.user_input_area,
            state=tk.DISABLED,
            show='*',
            textvariable=self.password_var,
            width=35,
        )
        self.password_entry.grid(row=1, column=1, pady=5, padx=5, sticky='w')

        # btn area
        self.btn_area = tk.Frame(self.main_frame, bg=self.bg_color)
        self.btn_area.grid(row=2, column=0, sticky='news', padx=20)
        self.btn_area.rowconfigure(0, weight=1)
        self.btn_area.columnconfigure(0, weight=1)
        self.btn_area.columnconfigure(1, weight=1)

        self.btn_config = tk.Button(self.btn_area, text='Config', command=self.show_config)
        self.btn_config.grid(row=0, column=0, sticky='e')
        self.btn_login = tk.Button(self.btn_area, text='Login', command=self.login_user)
        self.btn_login.grid(row=0, column=1)

        # hint area
        self.hint_area = tk.Frame(self.main_frame, bg=self.bg_color)
        self.hint_area.grid(row=3, column=0, sticky='news', )

        self.hint_area.rowconfigure(0, weight=1)
        self.hint_area.columnconfigure(0, weight=1)
        self.hint_default = 'Please input your username, and press Login to login,' \
                            ' or press Register button to register a new user.'
        self.hint_var = tk.StringVar(
            value=self.hint_default)
        self.hint_label = tk.Label(
            self.hint_area,
            textvariable=self.hint_var, justify='left',
            wraplength=300,
            bg=self.bg_color,
        )
        self.hint_label.grid(row=0, column=0, sticky='ew', padx=10)

    def show_config(self):
        print('config')
        self.btn_config.config(state=tk.DISABLED)
        config_window = ConfigWindow(self)
        self.wait_window(config_window)
        self.btn_config.config(state=tk.NORMAL)

    def login_user(self):
        global chat_client
        self.hint_var.set('')
        name = self.username_var.get()
        hint_msg = ''
        if name == '':
            hint_msg += 'Empty UserName Is Not Allowed'
            self.hint_var.set(hint_msg)
            return
        if name.upper() in ['Client'.upper(), '__SERVER__'.upper()]:
            hint_msg += 'Invalid UserName'
            self.hint_var.set(hint_msg)
            return
        chat_client.username = name
        st, msg = chat_client.init_connect()
        if not st:
            return self.hint_var.set(msg)
        st, msg = chat_client.login()
        if not st:
            hint_msg += msg
            self.hint_var.set(hint_msg)
            return
        else:
            self.destroy()
            return


