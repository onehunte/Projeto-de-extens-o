import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.core.window import Window
import webbrowser

# Define cores do tema fazenda
VERDE_ESCURO = (0.1, 0.3, 0.1, 1)  # Verde floresta
VERDE_CLARO = (0.7, 0.9, 0.7, 1)   # Verde suave
MARROM = (0.4, 0.3, 0.2, 1)        # Marrom terra
BEGE = (0.95, 0.93, 0.88, 1)       # Cor palha

Builder.load_string('''
#:import utils kivy.utils

<CustomButton@Button>:
    background_normal: ''
    background_color: 0.1, 0.3, 0.1, 1  # Verde escuro
    color: 0.95, 0.93, 0.88, 1  # Texto bege
    size_hint_y: None
    height: '50dp'
    font_size: '16sp'
    canvas.before:
        Color:
            rgba: 0.1, 0.3, 0.1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]

<EbookButton>:
    orientation: 'horizontal'
    spacing: 15
    padding: 10
    size_hint_y: None
    height: '70dp'
    
    canvas.before:
        Color:
            rgba: 0.95, 0.93, 0.88, 1  # Fundo bege
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]
        Color:
            rgba: 0.7, 0.9, 0.7, 0.3  # Borda verde clara
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 10)
            width: 1.5
    
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.7
        spacing: 5
        padding: 5
        
        Label:
            text: root.title
            color: 0.1, 0.3, 0.1, 1  # Texto verde escuro
            text_size: self.width, None
            halign: 'left'
            valign: 'middle'
            font_size: '16sp'
            bold: True
            shorten: True
            shorten_from: 'right'
    
    CustomButton:
        text: 'Abrir eBook'
        size_hint: 0.3, 0.8
        pos_hint: {'center_y': 0.5}
        on_press: root.on_press()

<EbookApp>:
    canvas.before:
        Color:
            rgba: 0.7, 0.9, 0.7, 1  # Fundo verde claro
        Rectangle:
            pos: self.pos
            size: self.size
    
    orientation: 'vertical'
    spacing: 15
    padding: 20
    
    BoxLayout:
        size_hint_y: None
        height: '100dp'
        orientation: 'vertical'
        spacing: 10
        
        Label:
            text: 'Biblioteca da Fazenda'
            font_size: '24sp'
            bold: True
            color: 0.1, 0.3, 0.1, 1  # Verde escuro
            size_hint_y: None
            height: '40dp'
        
        Label:
            id: status_label
            text: 'Lista de eBooks'
            font_size: '16sp'
            color: 0.4, 0.3, 0.2, 1  # Marrom
            size_hint_y: None
            height: '30dp'
    
    BoxLayout:
        padding: 5
        canvas.before:
            Color:
                rgba: 0.95, 0.93, 0.88, 0.7  # Bege transparente
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [15,]
        
        RecycleView:
            id: rv
            scroll_type: ['bars', 'content']
            scroll_wheel_distance: 114
            bar_width: 8
            bar_color: 0.1, 0.3, 0.1, 0.7  # Verde escuro transparente
            bar_inactive_color: 0.1, 0.3, 0.1, 0.2
            viewclass: 'EbookButton'
            
            RecycleBoxLayout:
                default_size: None, dp(70)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'
                spacing: 10
                padding: 10
    
    CustomButton:
        text: 'Atualizar Biblioteca'
        size_hint_x: 0.5
        pos_hint: {'center_x': 0.5}
        on_press: root.populate_ebooks()
''')

class EbookButton(RecycleDataViewBehavior, BoxLayout):
    title = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ebook_path = ""
        
    def refresh_view_attrs(self, rv, index, data):
        self.title = data['titulo']
        self.ebook_path = data['arquivo_path']
        return super().refresh_view_attrs(rv, index, data)
        
    def on_press(self):
        if self.ebook_path:
            webbrowser.open(self.ebook_path)
        else:
            print("Arquivo PDF não encontrado!")

class EbookApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.clearcolor = (0.7, 0.9, 0.7, 1)  # Fundo verde claro
        self.populate_ebooks()
    
    def populate_ebooks(self, *args):
        try:
            response = requests.get("http://localhost:5000/ebooks")
            if response.status_code == 200:
                ebooks = response.json()
                if ebooks:
                    self.ids.rv.data = [
                        {
                            'titulo': ebook['titulo'],
                            'arquivo_path': ebook['arquivo_path']
                        }
                        for ebook in ebooks
                    ]
                    self.ids.status_label.text = f"Biblioteca atualizada • {len(ebooks)} livros disponíveis"
                else:
                    self.ids.status_label.text = "A biblioteca está vazia"
                    self.ids.rv.data = []
            else:
                self.ids.status_label.text = f"Erro ao atualizar a biblioteca: {response.status_code}"
        except Exception as e:
            self.ids.status_label.text = f"Erro de conexão: {str(e)}"
            self.ids.rv.data = []

class MyEbookApp(App):
    def build(self):
        return EbookApp()

if __name__ == "__main__":
    MyEbookApp().run()