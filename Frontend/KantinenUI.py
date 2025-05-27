
from kivy.config import Config
Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '600')
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'borderless', '1')        # Kein Fensterrahmen

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import requests

class KantinenUI(App):
    def build(self):
        self.total = 0.0
        self.items = []
        self.item_counts = {}
        self.active_category = "Getränke"
        self.user_id = None
        self.user_name = None
        Clock.schedule_once(lambda dt: self.load_users(), 0.1)
        Clock.schedule_interval(lambda dt: self.load_users(), 150)

        self.products_by_category = {
            "Getränke": {},
            "Snacks": {},
            "Eis": {}
        }

        self.category_colors = {
            "Getränke": (0.2, 0.6, 1, 1),
            "Snacks": (1, 0.6, 0.2, 1),
            "Eis": (0.6, 0.2, 1, 1)
        }

        self.category_buttons = {}
        self.root = BoxLayout(orientation='horizontal', padding=10, spacing=10)

        # Linke Seite
        left_area = BoxLayout(orientation='vertical', size_hint=(0.7, 1), spacing=10)

        self.header = Label(text="Willkommen!", font_size='24sp', size_hint=(1, 0.1))
        left_area.add_widget(self.header)

        cat_buttons = BoxLayout(size_hint=(1, 0.15), spacing=10, padding=5)
        for category in self.products_by_category.keys():
            btn = Button(
                text=category,
                background_color=self.category_colors.get(category, (0.5, 0.5, 0.5, 1)),
                color=(1, 1, 1, 1),
                font_size='18sp'
            )
            btn.bind(on_press=self.switch_category)
            self.category_buttons[category] = btn
            cat_buttons.add_widget(btn)
        left_area.add_widget(cat_buttons)

        self.product_area = BoxLayout(size_hint=(1, 0.4))
        self.load_products()
        left_area.add_widget(self.product_area)

        # Rechte Seite
        right_area = BoxLayout(orientation='vertical', size_hint=(0.3, 1), padding=(10, 0))

        change_user_btn = Button(
            text="Benutzer wechseln",
            size_hint=(1, None),
            height=50,
            background_color=(0.2, 0.2, 0.8, 1),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        change_user_btn.bind(on_press=lambda instance: self.select_user_popup())
        right_area.add_widget(change_user_btn)

        self.summary = Label(
            text="Gesamt: € 0.00",
            font_size='20sp',
            halign='left',
            valign='top'
        )
        self.summary.bind(size=self.summary.setter('text_size'))
        right_area.add_widget(self.summary)

        bottom_controls = BoxLayout(orientation='vertical', size_hint=(1, None), height=100, spacing=10)
        back_button = Button(text="Storno", size_hint=(1, None), height=90, background_color=(0.7, 0, 0, 1))
        back_button.bind(on_press=self.cancel_transaction)
        finish = Button(text="Buchen", size_hint=(1, None), height=100, background_color=(0, 0.5, 1, 1))
        finish.bind(on_press=self.finish)
        bottom_controls.add_widget(back_button)
        bottom_controls.add_widget(finish)
        right_area.add_widget(bottom_controls)

        self.root.add_widget(left_area)
        self.root.add_widget(right_area)

        self.load_products_from_backend()
        Clock.schedule_interval(lambda dt: self.load_products_from_backend(), 120)
        self.register_activity_listeners()
        self.reset_inactivity_timer()


        return self.root

    
    def load_users(self):
        try:
            response = requests.get("http://localhost:8000/users")
            if response.status_code == 200:
                self.users = response.json()
                self.show_rfid_popup()
            else:
                self.users = []
                print("Fehler beim Laden der Nutzer:", response.text)
        except Exception as e:
            self.users = []
            print("Fehler beim Abrufen der Nutzer:", e)

    def select_user_popup(self):
            from kivy.uix.popup import Popup
            from kivy.uix.spinner import Spinner
            from kivy.uix.boxlayout import BoxLayout

            layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
            usernames = [user["username"] for user in self.users]
            user_dict = {user["username"]: user for user in self.users}
            spinner = Spinner(text=usernames[0] if usernames else "Keine Benutzer verfügbar", values=usernames, size_hint=(1, None), height=44, font_size='18sp')
            ok_button = Button(text="OK", size_hint=(1, None), height=44)
            layout.add_widget(spinner)
            layout.add_widget(ok_button)

            popup = Popup(title='Benutzer auswählen', content=layout, size_hint=(None, None), size=(500, 250), auto_dismiss=False)

            def set_user(instance):
                name = spinner.text
                selected = user_dict.get(name)
                if selected:
                    self.user_id = selected["id"]
                    self.user_name = selected["username"]
                    self.items = []
                    self.total = 0.0
                    self.header.text = f"Willkommen, {self.user_name}!"
                    self.update_summary()
                    popup.dismiss()

            ok_button.bind(on_press=set_user)
            popup.open()
   
    def show_rfid_popup(self):
        
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        from kivy.core.window import Window

        self.rfid_buffer = ""
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.rfid_status = Label(text="Bitte RFID scannen...", font_size='20sp')
        manual_button = Button(text="Manuell einloggen", size_hint=(1, None), height=44)

        layout.add_widget(self.rfid_status)
        layout.add_widget(manual_button)

        self.rfid_popup = Popup(title='RFID Login', content=layout, size_hint=(None, None), size=(400, 200), auto_dismiss=False)

        def manual_login(instance):
            self.rfid_popup.dismiss()
            self.select_user_popup()

        manual_button.bind(on_press=manual_login)
        self.rfid_popup.open()
        Window.bind(on_key_down=self.handle_rfid_key)

    def handle_rfid_key(self, window, key, scancode, codepoint, modifiers):
        if key == 13:  # Enter
            rfid = self.rfid_buffer.strip()
            self.rfid_buffer = ""
            matched = next((u for u in self.users if u.get("rfid") == rfid), None)
            if matched:
                self.user_id = matched["id"]
                self.user_name = matched["username"]
                self.items = []
                self.total = 0.0
                self.header.text = f"Willkommen, {self.user_name}!"
                self.update_summary()
                self.rfid_status.text = f"Eingeloggt: {self.user_name}"
                self.rfid_popup.dismiss()
                from kivy.core.window import Window
                Window.unbind(on_key_down=self.handle_rfid_key)
            else:
                self.rfid_status.text = "Unbekanntes RFID – erneut versuchen"
        elif codepoint:
            self.rfid_buffer += codepoint

    def reset_inactivity_timer(self, *args):
        from kivy.clock import Clock
        if hasattr(self, 'inactivity_event') and self.inactivity_event:
            self.inactivity_event.cancel()
        self.inactivity_event = Clock.schedule_once(self.perform_auto_logout, 180)

    def perform_auto_logout(self, *args):
        self.items = []
        self.total = 0.0
        self.user_id = None
        self.user_name = None
        self.update_summary()
        self.header.text = "Automatischer Logout wegen Inaktivität"
        self.show_rfid_popup()

    def register_activity_listeners(self):
        from kivy.core.window import Window
        Window.bind(on_touch_down=lambda *x: self.reset_inactivity_timer())
        Window.bind(on_key_down=lambda *x: self.reset_inactivity_timer())

    def load_products_from_backend(self, *args):
        try:
            response = requests.get("http://localhost:8000/products")
            if response.status_code == 200:
                products = response.json()
                self.products_by_category = {"Getränke": {}, "Snacks": {}, "Eis": {}}
                for product in products:
                    category = product.get("category", "Sonstiges")
                    if category not in self.products_by_category:
                        self.products_by_category[category] = {}
                    self.products_by_category[category][product["name"]] = {
                        "id": product["id"],
                        "price": product["price"],
                        "name": product["name"]
                    }
                self.load_products()
        except Exception as e:
            print("Fehler beim Laden der Produkte:", e)

    def load_products(self):
        self.product_area.clear_widgets()
        products = self.products_by_category.get(self.active_category, {})
        grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        for name, data in products.items():
            row = BoxLayout(size_hint_y=None, height=100, spacing=10)
            product_btn = Button(
                text=f"{name} (€{data['price']:.2f})",
                size_hint_x=0.5,
                background_color=self.category_colors.get(self.active_category, (0.5, 0.5, 0.5, 1)),
                color=(1, 1, 1, 1)
            )
            minus_btn = Button(text="-", size_hint_x=0.1)
            plus_btn = Button(text="+", size_hint_x=0.1)
            qty_label = Label(text=str(self.item_counts.get(data['id'], 0)), size_hint_x=0.3)

            def make_update_fn(product, delta):
                def update_quantity(instance):
                    pid = product['id']
                    self.item_counts[pid] = self.item_counts.get(pid, 0) + delta
                    if self.item_counts[pid] <= 0:
                        self.item_counts.pop(pid, None)
                    self.items = []
                    self.total = 0.0
                    for cid, count in self.item_counts.items():
                        for cat_items in self.products_by_category.values():
                            for prod in cat_items.values():
                                if prod['id'] == cid:
                                    self.items.extend([prod] * count)
                                    self.total += prod['price'] * count
                    self.load_products()
                    self.update_summary()
                return update_quantity

            product_btn.bind(on_press=make_update_fn(data, 1))
            minus_btn.bind(on_press=make_update_fn(data, -1))
            plus_btn.bind(on_press=make_update_fn(data, 1))
            row.add_widget(product_btn)
            row.add_widget(minus_btn)
            row.add_widget(qty_label)
            row.add_widget(plus_btn)
            grid.add_widget(row)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(grid)
        self.product_area.add_widget(scroll)

        for cat, btn in self.category_buttons.items():
            btn.background_color = self.category_colors.get(cat, (0.5, 0.5, 0.5, 1))
            if cat == self.active_category:
                btn.background_color = [0, 0.8, 0, 1]

    def switch_category(self, instance):
        self.active_category = instance.text
        self.load_products()

    def finish(self, instance):
        try:
            product_data = [{"product_id": item["id"], "product_name": item["name"], "price": item["price"]} for item in self.items]
            payload = {"user_id": self.user_id, "items": product_data, "total": self.total}
            response = requests.post("http://localhost:8000/transaction", json=payload)
            if response.status_code == 200:
                print("Transaktion erfolgreich gespeichert.")
        except Exception as e:
            print("Netzwerkfehler:", e)

        self.items = []
        self.total = 0.0
        self.update_summary()
        self.user_id = None
        self.user_name = None
        self.select_user_popup()

    def cancel_transaction(self, instance):
        self.items = []
        self.total = 0.0
        self.update_summary()

    def update_summary(self):
        text = f"Benutzer: {self.user_name or '–'}\n\nEinkauf:\n"
        for item in self.items:
            text += f"{item['name']} - € {item['price']:.2f}\n"
        text += f"\nGesamt: € {self.total:.2f}"
        self.summary.text = text

if __name__ == '__main__':
    KantinenUI().run()
