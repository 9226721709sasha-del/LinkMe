"""
LinkMe - Мессенджер для Android
Исправленная версия - работает и на PC для тестирования
"""

import socket
import threading
from datetime import datetime
import os
import json
import base64
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.uix.floatlayout import FloatLayout

# Устанавливаем размер окна для тестирования на PC
Window.size = (400, 700)

# Цветовая схема
COLORS = {
    'bg': '#1a1a2e',
    'card': '#16213e',
    'header': '#0f3460',
    'input': '#1a1a2e',
    'accent': '#e94560',
    'secondary': '#533483',
    'text': '#ffffff',
    'text_secondary': '#a0a0a0',
    'my_msg_bg': '#e94560',
    'other_msg_bg': '#16213e',
}


class RoundedButton(Button):
    """Овальная кнопка"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.size_hint_y = None
        self.height = dp(50)

        with self.canvas.before:
            self.bg_color = Color(*get_color_from_hex(COLORS['accent']))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(25)])

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class RoundedTextField(TextInput):
    """Овальное поле ввода"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.padding = [dp(15), dp(12), dp(15), dp(12)]
        self.multiline = False
        self.size_hint_y = None
        self.height = dp(50)

        with self.canvas.before:
            self.bg_color = Color(*get_color_from_hex(COLORS['input']))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(25)])

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class ChatBubble(BoxLayout):
    """Облачко сообщения"""
    def __init__(self, text, timestamp, is_my, sender_name="", **kwargs):
        super().__init__(**kwargs)

        self.size_hint_y = None
        self.height = dp(50)
        self.padding = [dp(10), dp(5)]

        bubble = BoxLayout(
            orientation='vertical',
            size_hint_x=0.75,
            size_hint_y=None,
            height=dp(50),
            padding=[dp(12), dp(8)]
        )

        with bubble.canvas.before:
            Color(*get_color_from_hex(COLORS['my_msg_bg'] if is_my else COLORS['other_msg_bg']))
            self.bubble_rect = RoundedRectangle(pos=bubble.pos, size=bubble.size, radius=[dp(15)])

        bubble.bind(pos=self.update_bubble_rect, size=self.update_bubble_rect)

        if not is_my and sender_name:
            name_label = Label(
                text=sender_name,
                color=get_color_from_hex(COLORS['secondary']),
                size_hint_y=None,
                height=dp(20),
                font_size=dp(11),
                halign='left',
                bold=True
            )
            name_label.bind(size=name_label.setter('text_size'))
            bubble.add_widget(name_label)

        msg_label = Label(
            text=text,
            color=(1, 1, 1, 1),
            font_size=dp(12),
            halign='left',
            valign='middle',
            text_size=(Window.width * 0.65, None)
        )
        msg_label.bind(size=msg_label.setter('text_size'))
        bubble.add_widget(msg_label)

        time_label = Label(
            text=timestamp,
            color=get_color_from_hex(COLORS['text_secondary']),
            size_hint_y=None,
            height=dp(15),
            font_size=dp(9),
            halign='right'
        )
        time_label.bind(size=time_label.setter('text_size'))
        bubble.add_widget(time_label)

        if is_my:
            bubble.pos_hint = {'right': 1}
        else:
            bubble.pos_hint = {'left': 0}

        self.add_widget(bubble)

    def update_bubble_rect(self, instance, value):
        self.bubble_rect.pos = instance.pos
        self.bubble_rect.size = instance.size


class LoginScreen(Screen):
    """Экран регистрации"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'login'

        with self.canvas.before:
            Color(*get_color_from_hex(COLORS['bg']))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        # Центрируем содержимое
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))

        # Отступ сверху
        layout.add_widget(Label(size_hint_y=None, height=dp(100)))

        title = Label(
            text="LinkMe",
            font_size=dp(42),
            color=get_color_from_hex(COLORS['accent']),
            size_hint_y=None,
            height=dp(80)
        )
        layout.add_widget(title)

        subtitle = Label(
            text="Welcome!",
            font_size=dp(18),
            color=get_color_from_hex(COLORS['text_secondary']),
            size_hint_y=None,
            height=dp(30)
        )
        layout.add_widget(subtitle)

        # Поле ввода имени
        layout.add_widget(Label(
            text="Your Name:",
            color=get_color_from_hex(COLORS['text']),
            font_size=dp(14),
            size_hint_y=None,
            height=dp(30),
            halign='left'
        ))

        self.name_input = RoundedTextField(
            hint_text="Enter your name",
            foreground_color=get_color_from_hex(COLORS['text']),
            hint_text_color=get_color_from_hex(COLORS['text_secondary']),
            font_size=dp(14)
        )
        layout.add_widget(self.name_input)

        # Кнопка регистрации
        self.register_btn = RoundedButton(
            text="REGISTER",
            font_size=dp(14),
            bold=True
        )
        self.register_btn.bind(on_release=self.do_register)
        layout.add_widget(self.register_btn)

        layout.add_widget(Label(size_hint_y=None, height=dp(100)))

        self.add_widget(layout)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def do_register(self, instance):
        name = self.name_input.text.strip()
        if not name:
            print("Enter name")
            return

        self.register_btn.text = "WAIT..."
        self.register_btn.disabled = True

        def reg_thread():
            try:
                s = socket.socket()
                s.settimeout(10)
                app = App.get_running_app()
                s.connect((app.SERVER, app.PORT))
                s.send(f"reg|{name}\n".encode())
                data = s.recv(4096).decode()
                s.close()

                parts = data.strip().split('|')
                if parts[0] == 'ok':
                    app.my_code = parts[1]
                    app.my_name = name
                    app.save_code()
                    Clock.schedule_once(lambda dt: app.do_login(), 0)
                else:
                    Clock.schedule_once(lambda dt: self.reset_button(), 0)
                    print("Registration error")
            except Exception as e:
                print(f"Error: {e}")
                Clock.schedule_once(lambda dt: self.reset_button(), 0)

        threading.Thread(target=reg_thread, daemon=True).start()

    def reset_button(self):
        self.register_btn.text = "REGISTER"
        self.register_btn.disabled = False


class ProfileScreen(Screen):
    """Экран настроек профиля"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'profile'

        with self.canvas.before:
            Color(*get_color_from_hex(COLORS['bg']))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        # Основной вертикальный layout
        main_layout = BoxLayout(orientation='vertical')

        # Заголовок
        header = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(10))
        header.canvas.before.add(Color(*get_color_from_hex(COLORS['header'])))
        header.canvas.before.add(RoundedRectangle(pos=header.pos, size=header.size))

        back_btn = RoundedButton(text="BACK", size_hint=(None, None), size=(dp(70), dp(40)), height=dp(40), font_size=dp(12))
        back_btn.bind(on_release=lambda x: self.go_back())
        header.add_widget(back_btn)

        title = Label(text="Profile", color=get_color_from_hex(COLORS['text']), font_size=dp(18), bold=True)
        header.add_widget(title)
        header.add_widget(Label(size_hint_x=0.1))

        main_layout.add_widget(header)

        # Контент с прокруткой
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # Аватар
        avatar_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100))
        avatar = Label(text="User", font_size=dp(40), size_hint_y=None, height=dp(80))
        avatar_layout.add_widget(avatar)
        content.add_widget(avatar_layout)

        # ID карточка
        id_card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=dp(15), spacing=dp(5))
        id_card.canvas.before.add(Color(*get_color_from_hex(COLORS['card'])))
        id_card.canvas.before.add(RoundedRectangle(pos=id_card.pos, size=id_card.size, radius=[dp(15)]))

        id_card.add_widget(Label(text="Your ID:", color=get_color_from_hex(COLORS['text_secondary']), font_size=dp(12), size_hint_y=None, height=dp(25)))
        self.id_label = Label(text="", color=get_color_from_hex(COLORS['text']), font_size=dp(14), bold=True, size_hint_y=None, height=dp(35))
        id_card.add_widget(self.id_label)
        content.add_widget(id_card)

        # Имя карточка
        name_card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150), padding=dp(15), spacing=dp(10))
        name_card.canvas.before.add(Color(*get_color_from_hex(COLORS['card'])))
        name_card.canvas.before.add(RoundedRectangle(pos=name_card.pos, size=name_card.size, radius=[dp(15)]))

        name_card.add_widget(Label(text="Your Name:", color=get_color_from_hex(COLORS['text_secondary']), font_size=dp(12), size_hint_y=None, height=dp(25)))
        self.name_input = RoundedTextField(text="", font_size=dp(14))
        name_card.add_widget(self.name_input)
        content.add_widget(name_card)

        # Кнопка сохранения
        save_btn = RoundedButton(text="SAVE", font_size=dp(14), bold=True)
        save_btn.bind(on_release=self.save_profile)
        content.add_widget(save_btn)

        content.add_widget(Label(size_hint_y=None, height=dp(50)))

        scroll.add_widget(content)
        main_layout.add_widget(scroll)

        self.add_widget(main_layout)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def on_enter(self):
        app = App.get_running_app()
        self.id_label.text = app.my_code if app.my_code else "No ID"
        self.name_input.text = app.my_name if app.my_name else ""

    def save_profile(self, instance):
        new_name = self.name_input.text.strip()
        if new_name and new_name != App.get_running_app().my_name:
            try:
                App.get_running_app().sock.send(f"change_name|{new_name}\n".encode())
                App.get_running_app().my_name = new_name
                print("Name changed!")
                self.go_back()
            except Exception as e:
                print(f"Error: {e}")

    def go_back(self):
        App.get_running_app().sm.current = 'chat'


class SearchScreen(Screen):
    """Экран поиска пользователей"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search'

        with self.canvas.before:
            Color(*get_color_from_hex(COLORS['bg']))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        # Основной вертикальный layout
        main_layout = BoxLayout(orientation='vertical')

        # Заголовок
        header = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(10))
        header.canvas.before.add(Color(*get_color_from_hex(COLORS['header'])))
        header.canvas.before.add(RoundedRectangle(pos=header.pos, size=header.size))

        back_btn = RoundedButton(text="BACK", size_hint=(None, None), size=(dp(70), dp(40)), height=dp(40), font_size=dp(12))
        back_btn.bind(on_release=lambda x: self.go_back())
        header.add_widget(back_btn)

        title = Label(text="Find Friends", color=get_color_from_hex(COLORS['text']), font_size=dp(18), bold=True)
        header.add_widget(title)
        header.add_widget(Label(size_hint_x=0.1))

        main_layout.add_widget(header)

        # Контент с прокруткой
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # Пояснение
        info = Label(
            text="Enter friend's ID to add chat",
            color=get_color_from_hex(COLORS['text_secondary']),
            font_size=dp(12),
            size_hint_y=None,
            height=dp(50)
        )
        content.add_widget(info)

        # Поле ввода ID друга
        content.add_widget(Label(
            text="Friend's ID:",
            color=get_color_from_hex(COLORS['text']),
            font_size=dp(14),
            size_hint_y=None,
            height=dp(30),
            halign='left'
        ))

        self.code_input = RoundedTextField(
            hint_text="Enter ID here",
            font_size=dp(14)
        )
        content.add_widget(self.code_input)

        # Кнопка поиска
        search_btn = RoundedButton(text="FIND", font_size=dp(14), bold=True)
        search_btn.bind(on_release=self.search_user)
        content.add_widget(search_btn)

        # Разделитель
        content.add_widget(Label(
            text="-" * 30,
            color=get_color_from_hex(COLORS['text_secondary']),
            size_hint_y=None,
            height=dp(30)
        ))

        # Информация о себе
        content.add_widget(Label(
            text="Your ID (share with friends):",
            color=get_color_from_hex(COLORS['text']),
            font_size=dp(14),
            size_hint_y=None,
            height=dp(30),
            halign='left'
        ))

        self.my_code_label = Label(
            text="",
            color=get_color_from_hex(COLORS['accent']),
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(self.my_code_label)

        content.add_widget(Label(size_hint_y=None, height=dp(50)))

        scroll.add_widget(content)
        main_layout.add_widget(scroll)

        self.add_widget(main_layout)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def on_enter(self):
        app = App.get_running_app()
        self.my_code_label.text = app.my_code if app.my_code else "No ID"

    def search_user(self, instance):
        code = self.code_input.text.strip()
        if not code:
            print("Enter ID")
            return

        if code == App.get_running_app().my_code:
            print("Cannot add yourself")
            return

        app = App.get_running_app()
        exists = any(c['code'] == code for c in app.chats)
        if exists:
            print("Chat already exists")
            return

        try:
            app.sock.send(f"new_chat|{code}\n".encode())
            print("Request sent!")
            self.code_input.text = ""
            Clock.schedule_once(lambda dt: self.go_back(), 2)
        except Exception as e:
            print(f"Error: {e}")

    def go_back(self):
        App.get_running_app().sm.current = 'chat'


class ChatWindow(FloatLayout):
    """Окно чата"""
    def __init__(self, chat, **kwargs):
        super().__init__(**kwargs)
        self.chat = chat

        with self.canvas.before:
            Color(*get_color_from_hex(COLORS['bg']))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        # Основной layout
        main_layout = BoxLayout(orientation='vertical')

        # Заголовок
        header = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(10))
        header.canvas.before.add(Color(*get_color_from_hex(COLORS['header'])))
        header.canvas.before.add(RoundedRectangle(pos=header.pos, size=header.size))

        back_btn = RoundedButton(text="BACK", size_hint=(None, None), size=(dp(70), dp(40)), height=dp(40), font_size=dp(12))
        back_btn.bind(on_release=lambda x: self.close())
        header.add_widget(back_btn)

        chat_title = Label(
            text=chat['name'],
            color=get_color_from_hex(COLORS['text']),
            font_size=dp(18),
            bold=True
        )
        header.add_widget(chat_title)
        header.add_widget(Label(size_hint_x=0.1))

        main_layout.add_widget(header)

        # Область сообщений
        self.messages_scroll = ScrollView()
        self.messages_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5), padding=[dp(10), dp(10)])
        self.messages_layout.bind(minimum_height=self.messages_layout.setter('height'))
        self.messages_scroll.add_widget(self.messages_layout)
        main_layout.add_widget(self.messages_scroll)

        # Панель ввода
        input_panel = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=dp(5), spacing=dp(5))
        input_panel.canvas.before.add(Color(*get_color_from_hex(COLORS['card'])))
        input_panel.canvas.before.add(RoundedRectangle(pos=input_panel.pos, size=input_panel.size))

        self.message_input = RoundedTextField(
            hint_text="Type message...",
            font_size=dp(14),
            size_hint_x=0.75
        )
        self.message_input.bind(on_text_validate=self.send_message)
        input_panel.add_widget(self.message_input)

        send_btn = RoundedButton(text="SEND", size_hint=(None, None), size=(dp(70), dp(50)), height=dp(50), font_size=dp(12))
        send_btn.bind(on_release=self.send_message)
        input_panel.add_widget(send_btn)

        main_layout.add_widget(input_panel)

        self.add_widget(main_layout)

        # Загружаем историю
        self.load_history()

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def load_history(self):
        app = App.get_running_app()
        if app.sock and app.connected:
            try:
                app.sock.send(f"get_history|{self.chat['code']}\n".encode())
            except:
                pass

    def add_message(self, text, timestamp, is_my, sender_name=""):
        msg = ChatBubble(text, timestamp, is_my, sender_name)
        self.messages_layout.add_widget(msg)
        self.messages_layout.height += dp(60)
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)

    def scroll_to_bottom(self):
        self.messages_scroll.scroll_y = 0

    def send_message(self, instance):
        text = self.message_input.text.strip()
        if not text:
            return

        self.message_input.text = ""

        try:
            app = App.get_running_app()
            app.sock.send(f"msg|{self.chat['code']}|{text}\n".encode())
            t = datetime.now().strftime("%H:%M")
            self.add_message(text, t, True)
        except Exception as e:
            print(f"Error: {e}")

    def close(self):
        app = App.get_running_app()
        app.root.remove_widget(self)
        app.chat_window = None


class ChatScreen(Screen):
    """Главный экран чатов"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'chat'

        with self.canvas.before:
            Color(*get_color_from_hex(COLORS['bg']))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        # Основной layout
        main_layout = BoxLayout(orientation='vertical')

        # Заголовок
        header = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(10))
        header.canvas.before.add(Color(*get_color_from_hex(COLORS['header'])))
        header.canvas.before.add(RoundedRectangle(pos=header.pos, size=header.size))

        # Кнопка профиля
        profile_btn = RoundedButton(text="PROFILE", size_hint=(None, None), size=(dp(80), dp(40)), height=dp(40), font_size=dp(11))
        profile_btn.bind(on_release=lambda x: self.open_profile())
        header.add_widget(profile_btn)

        # Заголовок
        self.chat_title = Label(
            text="LinkMe",
            color=get_color_from_hex(COLORS['text']),
            font_size=dp(18),
            bold=True
        )
        header.add_widget(self.chat_title)

        # Кнопка поиска
        search_btn = RoundedButton(text="FIND", size_hint=(None, None), size=(dp(70), dp(40)), height=dp(40), font_size=dp(11))
        search_btn.bind(on_release=lambda x: self.open_search())
        header.add_widget(search_btn)

        main_layout.add_widget(header)

        # Список чатов
        self.chats_layout = BoxLayout(orientation='vertical', spacing=dp(2), size_hint_y=None)
        self.chats_layout.bind(minimum_height=self.chats_layout.setter('height'))

        self.chats_scroll = ScrollView()
        self.chats_scroll.add_widget(self.chats_layout)
        main_layout.add_widget(self.chats_scroll)

        self.add_widget(main_layout)

        # Загружаем чаты
        Clock.schedule_once(lambda dt: self.update_chats_list(), 0.5)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def open_profile(self):
        App.get_running_app().sm.current = 'profile'

    def open_search(self):
        App.get_running_app().sm.current = 'search'

    def update_chats_list(self):
        self.chats_layout.clear_widgets()
        app = App.get_running_app()

        if not app.chats:
            empty_label = Label(
                text="No chats yet\nClick FIND to add friends",
                color=get_color_from_hex(COLORS['text_secondary']),
                font_size=dp(14),
                size_hint_y=None,
                height=dp(200)
            )
            self.chats_layout.add_widget(empty_label)
            self.chats_layout.height = dp(200)
            return

        total_height = 0
        for chat in app.chats:
            chat_card = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(70),
                padding=[dp(15), dp(10)],
                spacing=dp(15)
            )
            chat_card.canvas.before.add(Color(*get_color_from_hex(COLORS['card'])))
            chat_card.canvas.before.add(RoundedRectangle(pos=chat_card.pos, size=chat_card.size, radius=[dp(10)]))

            # Аватар
            avatar = Label(text="Chat", font_size=dp(16), size_hint_x=None, width=dp(60))
            chat_card.add_widget(avatar)

            # Информация
            info = BoxLayout(orientation='vertical', spacing=dp(5))
            name = Label(
                text=chat['name'],
                color=get_color_from_hex(COLORS['text']),
                font_size=dp(16),
                bold=True,
                halign='left',
                size_hint_y=None,
                height=dp(25)
            )
            name.bind(size=name.setter('text_size'))
            info.add_widget(name)

            code = Label(
                text=f"ID: {chat['code']}",
                color=get_color_from_hex(COLORS['text_secondary']),
                font_size=dp(10),
                halign='left',
                size_hint_y=None,
                height=dp(20)
            )
            code.bind(size=code.setter('text_size'))
            info.add_widget(code)

            chat_card.add_widget(info)

            # Делаем карточку кликабельной
            chat_card.bind(on_touch_down=lambda instance, touch, c=chat: self.on_chat_click(instance, touch, c))

            self.chats_layout.add_widget(chat_card)
            total_height += dp(70)

        self.chats_layout.height = total_height

    def on_chat_click(self, instance, touch, chat):
        if instance.collide_point(*touch.pos):
            self.open_chat_window(chat)

    def open_chat_window(self, chat):
        app = App.get_running_app()
        if app.chat_window:
            return
        chat_window = ChatWindow(chat)
        app.chat_window = chat_window
        app.root.add_widget(chat_window)

    def update_chats(self):
        self.update_chats_list()


class LinkMeApp(App):
    """Главное приложение"""

    SERVER = "31.76.244.208"
    PORT = 5555

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sock = None
        self.my_code = None
        self.my_name = None
        self.chats = []
        self.connected = False
        self.buffer = ""
        self.chat_window = None

    def build(self):
        self.title = "LinkMe"

        self.load_chats_from_file()

        # Создаём менеджер экранов
        self.sm = ScreenManager()
        self.sm.add_widget(LoginScreen(name='login'))
        self.sm.add_widget(ChatScreen(name='chat'))
        self.sm.add_widget(ProfileScreen(name='profile'))
        self.sm.add_widget(SearchScreen(name='search'))

        # Проверяем сохранённый код
        if os.path.exists("code.txt"):
            try:
                with open("code.txt", "r") as f:
                    self.my_code = f.read().strip()
                    self.do_login()
                    self.sm.current = 'chat'
            except:
                self.sm.current = 'login'
        else:
            self.sm.current = 'login'

        return self.sm

    def save_code(self):
        with open("code.txt", "w") as f:
            f.write(self.my_code)

    def save_chats_to_file(self):
        try:
            with open("my_chats.json", "w", encoding='utf-8') as f:
                json.dump(self.chats, f, ensure_ascii=False)
        except:
            pass

    def load_chats_from_file(self):
        try:
            if os.path.exists("my_chats.json"):
                with open("my_chats.json", "r", encoding='utf-8') as f:
                    self.chats = json.load(f)
            else:
                self.chats = []
        except:
            self.chats = []

    def do_login(self):
        def login_thread():
            try:
                self.sock = socket.socket()
                self.sock.settimeout(10)
                self.sock.connect((self.SERVER, self.PORT))
                self.sock.send(f"login|{self.my_code}\n".encode())
                data = self.sock.recv(4096).decode()

                parts = data.strip().split('|')
                if parts[0] == 'ok':
                    self.my_name = parts[1]
                    self.connected = True
                    threading.Thread(target=self.listen, daemon=True).start()
                    print("Login successful!")
                else:
                    print("Login error")
            except Exception as e:
                print(f"Error: {e}")

        threading.Thread(target=login_thread, daemon=True).start()

    def listen(self):
        while self.connected:
            try:
                self.sock.settimeout(1)
                data = self.sock.recv(65536).decode()
                if not data:
                    break

                self.buffer += data
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    if not line.strip():
                        continue

                    parts = line.split('|')
                    if len(parts) < 1:
                        continue

                    cmd = parts[0]

                    if cmd == 'chats':
                        if len(parts) > 1 and parts[1]:
                            for item in parts[1:]:
                                if '|' in item:
                                    code, name = item.split('|')
                                    exists = any(c['code'] == code for c in self.chats)
                                    if not exists:
                                        self.chats.append({'code': code, 'name': name})
                            self.save_chats_to_file()
                            Clock.schedule_once(lambda dt: self.update_chats_screen(), 0)

                    elif cmd == 'msg':
                        if len(parts) >= 5:
                            from_code = parts[1]
                            from_name = parts[2]
                            text = parts[3]
                            timestamp = int(parts[4])
                            t = datetime.fromtimestamp(timestamp).strftime("%H:%M")

                            if self.chat_window and self.chat_window.chat['code'] == from_code:
                                Clock.schedule_once(lambda dt, txt=text, tm=t, fn=from_name:
                                                  self.chat_window.add_message(txt, tm, False, fn), 0)

                    elif cmd == 'chat_created':
                        if len(parts) >= 3:
                            code = parts[1]
                            name = parts[2]
                            exists = any(c['code'] == code for c in self.chats)
                            if not exists:
                                self.chats.append({'code': code, 'name': name})
                                self.save_chats_to_file()
                                Clock.schedule_once(lambda dt: self.update_chats_screen(), 0)
                                print(f"New chat: {name}")

                    elif cmd == 'error':
                        print(f"Error: {parts[1] if len(parts) > 1 else 'Unknown'}")

            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error: {e}")
                break

    def update_chats_screen(self):
        if self.sm.current == 'chat':
            chat_screen = self.sm.get_screen('chat')
            chat_screen.update_chats()


if __name__ == "__main__":
    LinkMeApp().run()