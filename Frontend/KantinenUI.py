from kivy.config import Config
Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '600')
Config.set('graphics', 'resizable', False)

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import requests

class KantinenUI(App):
    def build(self):
        self.total = 0.0
        self.items = []
        self.active_category = "Getränke"
       

        # Kategorien mit Farben
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

        # Haupt-Layout horizontal: links = Buttons & Produkte, rechts = Summary
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

        back_button = Button(text="Zurück", size_hint=(1, 0.1), background_color=(0.7, 0, 0, 1))
        back_button.bind(on_press=self.cancel_transaction)
        left_area.add_widget(back_button)

        finish = Button(text="Abschließen", size_hint=(1, 0.1), background_color=(0, 0.5, 1, 1))
        finish.bind(on_press=self.finish)
        left_area.add_widget(finish)

        # Rechte Seite: Summary
        right_area = BoxLayout(orientation='vertical', size_hint=(0.3, 1), padding=(10, 0))
        self.summary = Label(
            text="Gesamt: € 0.00",
            font_size='20sp',
            halign='left',
            valign='top'
        )
        self.summary.bind(size=self.summary.setter('text_size'))
        right_area.add_widget(self.summary)

    # Zusammensetzen
        self.root.add_widget(left_area)
        self.root.add_widget(right_area)


        # Initialer Ladevorgang
        self.load_products_from_backend()

        # Wiederholtes Nachladen alle 2 Minuten
        Clock.schedule_interval(lambda dt: self.load_products_from_backend(), 120)

        return self.root

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
                else:
                    print("Fehler beim Abrufen der Produkte:", response.text)
            
        except Exception as e:
                print("Fehler beim Laden der Produkte:", e)

    def load_products(self):
        self.product_area.clear_widgets()
        products = self.products_by_category.get(self.active_category, {})

        grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        for name, data in products.items():
            btn = Button(
                text=f"{name}\n€ {data['price']:.2f}",
                size_hint_y=None,
                height=100,
                font_size='20sp'
            )
            btn.product_data = data  # 👈 HIER: zusätzliche Daten am Button speichern
            btn.bind(on_press=self.add_product)
            grid.add_widget(btn)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(grid)
        self.product_area.add_widget(scroll)

    def switch_category(self, instance):
        self.active_category = instance.text
        self.load_products()

        for cat, btn in self.category_buttons.items():
            if cat == self.active_category:
                btn.background_color = [0, 0.8, 0, 1]
            else:
                btn.background_color = self.category_colors.get(cat, (0.5, 0.5, 0.5, 1))

    def add_product(self, instance):
        data = instance.product_data
        self.items.append(data)
        self.total += data["price"]
        self.update_summary()

    def update_summary(self):
        text = "Einkauf:\n"
        for item in self.items:
            text += f"{item['name']} - € {item['price']:.2f}\n"
            text += f"\nGesamt: € {self.total:.2f}"
            self.summary.text = text

    def finish(self, instance):

        try:
            product_data = [{"product_id": item["id"], "product_name": item["name"]} for item in self.items]

            payload = {
                "user_id": 1,
                "items": product_data
            }

            response = requests.post("http://localhost:8000/transaction", json=payload)
            if response.status_code == 200:
                print("Transaktion erfolgreich gespeichert.")
            else:
                print("Fehler beim Senden:", response.text)
        except Exception as e:
            print("Netzwerkfehler:", e)

        self.items = []
        self.total = 0.0
        self.update_summary()


    def cancel_transaction(self, instance):
        print("Transaktion abgebrochen.")
        self.items = []
        self.total = 0.0
        self.update_summary()

if __name__ == '__main__':
    KantinenUI().run()
