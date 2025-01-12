import flet as ft
import os
import mysql.connector
from datetime import datetime
from pathlib import Path
import shutil

class DatabaseConfig:
    def __init__(self):
        self.connection = None
        self.upload_folder = "uploads"  # Pasta local para salvar os ebooks
        
        # Criar pasta de uploads se não existir
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

    def connect(self, host, user, password, database):
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.create_tables()
            return True
        except Exception as e:
            print(f"Erro na conexão: {e}")
            return False

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ebooks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                arquivo_path VARCHAR(255) NOT NULL,
                data_upload DATETIME NOT NULL,
                tamanho BIGINT NOT NULL,
                status VARCHAR(50) DEFAULT 'disponível'
            )
        ''')
        self.connection.commit()
        cursor.close()

class EbookManager:
    def __init__(self):
        self.db = DatabaseConfig()
        self.current_file = None

    def save_ebook(self, file_path, original_filename, file_size):
        try:
            cursor = self.db.connection.cursor()
            
            # Copiar arquivo para a pasta de uploads
            new_path = os.path.join(self.db.upload_folder, original_filename)
            shutil.copy2(file_path, new_path)
            
            # Inserir registro no banco
            cursor.execute('''
                INSERT INTO ebooks (titulo, arquivo_path, data_upload, tamanho, status)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                original_filename,
                new_path,
                datetime.now(),
                file_size,
                'disponível'
            ))
            
            self.db.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar ebook: {e}")
            return False

    def get_all_ebooks(self):
        try:
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM ebooks ORDER BY data_upload DESC')
            return cursor.fetchall()
        except Exception as e:
            print(f"Erro ao buscar ebooks: {e}")
            return []

    def delete_ebook(self, ebook_id):
        try:
            cursor = self.db.connection.cursor()
            
            # Primeiro, pegar o caminho do arquivo
            cursor.execute('SELECT arquivo_path FROM ebooks WHERE id = %s', (ebook_id,))
            result = cursor.fetchone()
            
            if result:
                file_path = result[0]
                # Deletar o arquivo físico
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # Deletar o registro do banco
                cursor.execute('DELETE FROM ebooks WHERE id = %s', (ebook_id,))
                self.db.connection.commit()
                
            cursor.close()
            return True
        except Exception as e:
            print(f"Erro ao deletar ebook: {e}")
            return False

def main(page: ft.Page):
    page.title = "Gerenciador de E-books"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1000
    page.window_height = 800
    page.padding = 20

    manager = EbookManager()
    
    # Campos de configuração do MySQL
    db_fields = {
        "host": ft.TextField(label="Host", value="localhost", width=300),
        "user": ft.TextField(label="Usuário", width=300),
        "password": ft.TextField(label="Senha", password=True, width=300),
        "database": ft.TextField(label="Nome do Banco", width=300)
    }

    # Componentes da interface
    file_picker = ft.FilePicker(
        on_result=lambda e: handle_file_picked(e)
    )
    page.overlay.append(file_picker)
    
    status_text = ft.Text()
    progress_bar = ft.ProgressBar(visible=False)
    books_list = ft.ListView(expand=True, spacing=10, padding=20)

    def show_message(msg, color="white"):
        status_text.value = msg
        status_text.color = color
        page.update()

    def handle_file_picked(e):
        if e.files:
            manager.current_file = e.files[0]
            show_message(f"Arquivo selecionado: {manager.current_file.name}")
            upload_button.disabled = False
            page.update()

    def connect_database(e):
        config = {field: db_fields[field].value for field in db_fields}
        if all(config.values()):
            if manager.db.connect(**config):
                show_message("Conexão com banco de dados estabelecida!", "green")
                config_view.visible = False
                main_view.visible = True
                load_books()
                page.update()
            else:
                show_message("Erro ao conectar ao banco de dados!", "red")
        else:
            show_message("Preencha todos os campos!", "red")

    def load_books():
        books_list.controls.clear()
        for book in manager.get_all_ebooks():
            books_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.BOOK),
                                title=ft.Text(book['titulo']),
                                subtitle=ft.Text(f"Enviado em: {book['data_upload'].strftime('%d/%m/%Y %H:%M')}")
                            ),
                            ft.Row([
                                ft.TextButton(
                                    "Excluir",
                                    icon=ft.icons.DELETE,
                                    on_click=lambda e, id=book['id']: delete_book(id)
                                )
                            ], alignment=ft.MainAxisAlignment.END)
                        ])
                    ),
                    margin=10
                )
            )
        page.update()

    def upload_ebook(e):
        if not manager.current_file:
            show_message("Nenhum arquivo selecionado!", "red")
            return

        progress_bar.visible = True
        upload_button.disabled = True
        page.update()

        try:
            if manager.save_ebook(
                manager.current_file.path,
                manager.current_file.name,
                manager.current_file.size
            ):
                show_message("E-book enviado com sucesso!", "green")
                load_books()
            else:
                show_message("Erro ao enviar e-book!", "red")
        except Exception as e:
            show_message(f"Erro no upload: {str(e)}", "red")
        finally:
            progress_bar.visible = False
            upload_button.disabled = False
            page.update()

    def delete_book(book_id):
        if manager.delete_ebook(book_id):
            show_message("E-book excluído com sucesso!", "green")
            load_books()
        else:
            show_message("Erro ao excluir e-book!", "red")

    # Botões principais
    config_button = ft.ElevatedButton(
        "Conectar ao Banco",
        on_click=connect_database,
        style=ft.ButtonStyle(
            color={
                ft.MaterialState.DEFAULT: ft.colors.WHITE,
                ft.MaterialState.HOVERED: ft.colors.WHITE,
            },
            bgcolor={
                ft.MaterialState.DEFAULT: ft.colors.BLUE,
                ft.MaterialState.HOVERED: ft.colors.BLUE_700,
            },
        )
    )

    upload_button = ft.ElevatedButton(
        "Fazer Upload",
        on_click=upload_ebook,
        disabled=True,
        style=ft.ButtonStyle(
            color={
                ft.MaterialState.DEFAULT: ft.colors.WHITE,
                ft.MaterialState.HOVERED: ft.colors.WHITE,
            },
            bgcolor={
                ft.MaterialState.DEFAULT: ft.colors.GREEN,
                ft.MaterialState.HOVERED: ft.colors.GREEN_700,
            },
        )
    )

    select_file_button = ft.ElevatedButton(
        "Selecionar E-book",
        icon=ft.icons.UPLOAD_FILE,
        on_click=lambda _: file_picker.pick_files(
            allowed_extensions=['pdf', 'epub', 'mobi'],
            allow_multiple=False
        )
    )

    # Views
    config_view = ft.Column([
        ft.Text("Configuração do Banco de Dados", size=24, weight=ft.FontWeight.BOLD),
        ft.Container(height=20),
        *[db_fields[field] for field in db_fields],
        ft.Container(height=20),
        config_button,
        status_text
    ])

    main_view = ft.Column([
        ft.Text("Gerenciador de E-books", size=24, weight=ft.FontWeight.BOLD),
        ft.Row([select_file_button, upload_button]),
        progress_bar,
        status_text,
        books_list
    ], visible=False)
    
    page.add(config_view, main_view)

if __name__ == '__main__':
    ft.app(target=main)