import flet as ft
import requests
import threading
import time
from datetime import datetime

SERVER_URL = "https://your-render-url.onrender.com"  # <-- Yaha apna Render URL daalna!

def main(page: ft.Page):
    page.title = "MyQchat"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 400
    page.window_height = 700

    current_user = {"user_id": None, "username": None}

    # LOGIN UI
    email_field = ft.TextField(label="Email", width=300)
    pass_field = ft.TextField(label="Password", password=True, width=300)
    status_text = ft.Text(value="", color=ft.colors.RED)

    def login_click(e):
        try:
            r = requests.post(f"{SERVER_URL}/api/login", json={"email": email_field.value, "password": pass_field.value}, timeout=10)
            data = r.json()
            if data.get("success"):
                current_user["user_id"] = data["user_id"]
                current_user["username"] = data["username"]
                page.go("/chats")
            else:
                status_text.value = data.get("msg", "Login failed")
                page.update()
        except Exception as ex:
            status_text.value = f"Server not reachable: {ex}"
            page.update()

    def register_click(e):
        try:
            r = requests.post(f"{SERVER_URL}/api/register", json={"email": email_field.value, "username": email_field.value.split("@")[0], "password": pass_field.value}, timeout=10)
            data = r.json()
            status_text.value = data.get("msg", "Done")
            page.update()
        except Exception as ex:
            status_text.value = f"Error: {ex}"
            page.update()

    login_view = ft.View("/",
        controls=[
            ft.Column([
                ft.Text("MyQchat", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("100% English - Simple Chat", size=14),
                email_field,
                pass_field,
                ft.ElevatedButton("Login", on_click=login_click, width=300),
                ft.TextButton("Register", on_click=register_click),
                status_text,
                ft.Text("Terms: Owner can view chats for moderation", size=10, color=ft.colors.GREY)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        ]
    )

    # CHATS UI (optimized - 50 messages only)
    chat_list = ft.ListView(expand=True, spacing=5, padding=10)
    msg_list = ft.ListView(expand=True, spacing=4, padding=10, auto_scroll=True)
    msg_input = ft.TextField(hint_text="Type message...", expand=True)
    page_num = [1]

    def load_chats():
        try:
            r = requests.get(f"{SERVER_URL}/api/chats", params={"user_id": current_user["user_id"]}, timeout=8)
            chats = r.json()
            chat_list.controls.clear()
            for c in chats[-50:]:  # last 50 chats only - optimization
                chat_list.controls.append(
                    ft.ListTile(title=ft.Text(c.get("name","Chat")), subtitle=ft.Text(f"ID:{c.get('id')}"), on_click=lambda e, cid=c.get('id'): open_chat(cid))
                )
            page.update()
        except Exception as ex:
            print(ex)

    def open_chat(chat_id):
        page_num[0]=1
        msg_list.controls.clear()
        page.go(f"/chat/{chat_id}")

    def load_msgs(chat_id):
        try:
            r = requests.get(f"{SERVER_URL}/api/messages", params={"chat_id": chat_id, "user_id": current_user["user_id"], "page": page_num[0]}, timeout=8)
            msgs = r.json()
            msg_list.controls.clear()
            for m in msgs:  # server already paginated 50
                msg_list.controls.append(ft.Text(f"{m.get('username')}: {m.get('text')}"))
            page.update()
        except Exception as ex:
            print(ex)

    def send_click(e):
        if not msg_input.value.strip():
            return
        # current chat id from route
        try:
            chat_id = int(page.route.split("/")[-1])
            requests.post(f"{SERVER_URL}/api/messages", json={"chat_id": chat_id, "sender_id": current_user["user_id"], "text": msg_input.value}, timeout=8)
            msg_input.value = ""
            load_msgs(chat_id)
        except Exception as ex:
            print(ex)

    def route_change(route):
        page.views.clear()
        if page.route == "/":
            page.views.append(login_view)
        elif page.route == "/chats":
            page.views.append(
                ft.View("/chats",
                    controls=[
                        ft.AppBar(title=ft.Text(f"Hi {current_user['username']}"), bgcolor=ft.colors.BLUE),
                        ft.ElevatedButton("Refresh", on_click=lambda e: load_chats()),
                        chat_list
                    ]
                )
            )
            threading.Thread(target=load_chats, daemon=True).start()
        elif page.route.startswith("/chat/"):
            chat_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(f"/chat/{chat_id}",
                    controls=[
                        ft.AppBar(title=ft.Text(f"Chat {chat_id}"), leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda e: page.go("/chats"))),
                        msg_list,
                        ft.Row([msg_input, ft.IconButton(ft.icons.SEND, on_click=send_click)]),
                        ft.Row([ft.ElevatedButton("Load more", on_click=lambda e: (page_num.__setitem__(0, page_num[0]+1), load_msgs(int(chat_id))))])
                    ]
                )
            )
            threading.Thread(target=lambda: load_msgs(int(chat_id)), daemon=True).start()
        page.update()

    page.on_route_change = route_change
    page.go(page.route)

ft.app(target=main)
  
