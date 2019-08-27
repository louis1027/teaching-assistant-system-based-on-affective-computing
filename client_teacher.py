import tkinter as tk
import sys
from tcp_client import ChatClient
chat_client = ChatClient('teacher')

import client_share
client_share.chat_client = chat_client
client_share.APP_TITLE = 'Teacher App'

if __name__ == '__main__':
    login_app = client_share.LoginWindow()
    try:
        login_app.mainloop()
    except tk.TclError:
        pass
    except KeyboardInterrupt:
        login_app.quit()
        sys.exit()
    if not chat_client.online:
        print('Not in Login')
        sys.exit()

    app = client_share.MainApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.quit()
