import os
import tkinter as tk
from tkinter import messagebox, simpledialog, colorchooser, Menu
import yaml
from modules.database import load_notes, save_notes

# Función para cargar la configuración desde un archivo YAML
def load_config():
    config_path = os.path.join("data", "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"No se encuentra el archivo de configuración: {config_path}")
    
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

# Función para guardar la configuración en un archivo YAML
def save_config(config):
    config_path = os.path.join("data", "config.yaml")
    with open(config_path, 'w') as file:
        yaml.safe_dump(config, file)

class Pynote:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.apply_theme(self.config['window']['theme'])  # Aplicar el tema desde la configuración
        self.root.title(self.config['window']['title'])  # Configurar el título de la ventana
        self.root.geometry(self.config['window']['size'])  # Configurar el tamaño de la ventana
        try:
            self.root.iconbitmap("icon.ico")  # Intentar cargar el ícono
        except tk.TclError as e:
            print("Error al cargar el icono:", e)

        self.notes = load_notes()  # Cargar las notas desde la base de datos
        self.current_note_index = None
        self.current_folder = None
        self.folder_stack = []  # Pila para gestionar la navegación por carpetas

        # Crear la barra de menú
        self.menu_bar = Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Menú de archivo
        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New Folder", command=self.add_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_closing)

        # Menú de configuración
        self.edit_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Config", menu=self.edit_menu)
        self.edit_menu.add_command(label="Change Theme", command=self.change_theme)
        self.edit_menu.add_command(label="Clear all", command=self.clear_all_notes)

        # Crear el marco para la lista de notas
        self.notes_list_frame = tk.Frame(root)
        self.notes_list_frame.pack(fill=tk.BOTH, expand=True)

        # Botón para agregar una nueva nota
        self.add_button = tk.Button(self.notes_list_frame, text="+", command=self.add_note)
        self.add_button.pack(fill=tk.X)

        # Botón para volver a la carpeta anterior
        self.back_button = tk.Button(self.notes_list_frame, text="Back", command=self.go_back)
        self.back_button.pack(fill=tk.X)
        self.back_button.pack_forget()  # Ocultar el botón al inicio

        # Lista de notas y carpetas
        self.notes_listbox = tk.Listbox(self.notes_list_frame)
        self.notes_listbox.pack(fill=tk.BOTH, expand=True)
        self.notes_listbox.bind("<<ListboxSelect>>", self.update_context_menu)
        self.notes_listbox.bind("<Double-1>", self.open_note_or_folder)
        self.notes_listbox.bind("<Button-3>", self.show_context_menu)

        self.load_notes_list()  # Cargar la lista de notas inicial

        # Menú contextual para las notas
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Rename", command=self.rename_note)
        self.fav_command_index = self.context_menu.index("end") + 1
        self.context_menu.add_command(label="Favourite", command=self.fav_note)
        self.context_menu.add_command(label="Change Color", command=self.change_color)
        self.context_menu.add_command(label="Delete", command=self.delete_note_or_folder)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # Confirmar al cerrar la ventana

    def apply_theme(self, theme):
        """Aplica el tema a la ventana principal."""
        if theme == "dark":
            self.root.tk_setPalette(background="#2e2e2e", foreground="#ffffff", activeBackground="#3e3e3e", activeForeground="#ffffff")
        else:
            self.root.tk_setPalette(background="#ffffff", foreground="#000000", activeBackground="#e0e0e0", activeForeground="#000000")

    def load_notes_list(self, folder=None):
        """Carga la lista de notas y carpetas en el Listbox."""
        self.notes_listbox.delete(0, tk.END)
        self.current_folder = folder

        if folder is None:
            items = self.notes
            self.back_button.pack_forget()
        else:
            items = folder.get('contents', [])
            self.back_button.pack(fill=tk.X)

        for i, item in enumerate(items):
            display_name = f"{i+1}. {item['title']}"
            if item.get('is_folder', False):
                display_name = f"[Folder] {item['title']}"
            if item.get('favourite', False):
                display_name += " ⭐"  # Añadir el emoji de estrella a las notas favoritas
            self.notes_listbox.insert(tk.END, display_name)
            self.notes_listbox.itemconfig(i, {'bg': item.get('color', 'white')})

    def add_note(self):
        """Agregar una nueva nota."""
        title = simpledialog.askstring("New Note", "Enter note title:")
        if title:
            new_note = {"title": title, "content": "", "color": "white", "favourite": False}
            if self.current_folder is None:
                self.notes.append(new_note)
            else:
                self.current_folder['contents'].append(new_note)
            self.load_notes_list(self.current_folder)
            save_notes(self.notes)

    def rename_note(self):
        """Renombrar una nota existente."""
        selection = self.notes_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if self.current_folder is None:
            item = self.notes[index]
        else:
            item = self.current_folder['contents'][index]

        new_title = simpledialog.askstring("Rename Note", "Enter new title:", initialvalue=item['title'])
        if new_title:
            item['title'] = new_title
            self.load_notes_list(self.current_folder)
            save_notes(self.notes)

    def fav_note(self):
        """Marcar o desmarcar una nota como favorita."""
        selection = self.notes_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if self.current_folder is None:
            item = self.notes[index]
        else:
            item = self.current_folder['contents'][index]

        # Marca o desmarca la nota como favorita
        item['favourite'] = not item.get('favourite', False)
        self.load_notes_list(self.current_folder)
        save_notes(self.notes)
        self.update_context_menu()

    def update_context_menu(self, event=None):
        """Actualizar el menú contextual según el estado de la nota seleccionada."""
        selection = self.notes_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if self.current_folder is None:
            item = self.notes[index]
        else:
            item = self.current_folder['contents'][index]

        fav_label = "Unfavourite" if item.get('favourite', False) else "Favourite"
        self.context_menu.entryconfig(self.fav_command_index, label=fav_label)

    def change_color(self):
        """Cambiar el color de fondo de la nota seleccionada."""
        selection = self.notes_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if self.current_folder is None:
            item = self.notes[index]
        else:
            item = self.current_folder['contents'][index]

        color = colorchooser.askcolor()[1]
        if color:
            item['color'] = color
            self.load_notes_list(self.current_folder)
            save_notes(self.notes)

    def open_note_or_folder(self, event=None):
        """Abrir una nota o carpeta al hacer doble clic."""
        selection = self.notes_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if self.current_folder is None:
            item = self.notes[index]
        else:
            item = self.current_folder['contents'][index]

        if item.get('is_folder', False):
            self.folder_stack.append(self.current_folder)
            self.load_notes_list(item)
        else:
            self.open_note_editor(index, item)

    def go_back(self):
        """Volver a la carpeta anterior en la pila."""
        if self.folder_stack:
            self.load_notes_list(self.folder_stack.pop())

    def open_note_editor(self, index, note):
        """Abrir el editor para una nota específica."""
        editor_window = tk.Toplevel(self.root)
        editor_window.title(note["title"])
        editor_window.geometry(self.config['editor']['size'])
        self.apply_theme_to_editor(editor_window, self.config['window']['theme'])

        note_text = tk.Text(editor_window, wrap=tk.WORD, font=self.config['editor']['font'])
        note_text.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        note_text.insert(tk.END, note["content"])
        note_text.configure(bg=note.get("color", "white"))

        editor_window.grid_rowconfigure(0, weight=1)
        editor_window.grid_columnconfigure(0, weight=1)

        def save_note():
            """Guardar los cambios realizados en la nota."""
            note["content"] = note_text.get(1.0, tk.END).strip()
            note["color"] = note_text.cget("bg")
            save_notes(self.notes)
            self.load_notes_list(self.current_folder)
            editor_window.destroy()
            messagebox.showinfo("Success", "Note saved successfully")

        def delete_note():
            """Eliminar la nota actual."""
            if messagebox.askyesno("Delete Note", "Are you sure you want to delete this note?"):
                if self.current_folder is None:
                    del self.notes[index]
                else:
                    del self.current_folder['contents'][index]
                self.load_notes_list(self.current_folder)
                save_notes(self.notes)
                editor_window.destroy()
                messagebox.showinfo("Success", "Note deleted successfully")

        def choose_color():
            """Elegir un nuevo color de fondo para la nota."""
            color = colorchooser.askcolor()[1]
            if color:
                note_text.configure(bg=color)

        # Botones para guardar, eliminar y cambiar el color
        save_button = tk.Button(editor_window, text="Save", command=save_note)
        save_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        delete_button = tk.Button(editor_window, text="Delete", command=delete_note)
        delete_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        color_button = tk.Button(editor_window, text="Choose Color", command=choose_color)
        color_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        editor_window.protocol("WM_DELETE_WINDOW", save_note)  # Guardar la nota al cerrar el editor

    def apply_theme_to_editor(self, window, theme):
        """Aplicar el tema al editor de notas."""
        if theme == "dark":
            window.configure(bg="#2e2e2e")
            for child in window.winfo_children():
                child.configure(bg="#2e2e2e", fg="#ffffff", activebackground="#3e3e3e", activeforeground="#ffffff")
        else:
            window.configure(bg="#ffffff")
            for child in window.winfo_children():
                child.configure(bg="#ffffff", fg="#000000", activebackground="#e0e0e0", activeforeground="#000000")

    def change_theme(self):
        """Cambiar el tema de la aplicación."""
        new_theme = "dark" if self.config['window']['theme'] == "light" else "light"
        self.config['window']['theme'] = new_theme
        self.apply_theme(new_theme)
        save_config(self.config)

    def add_folder(self):
        """Agregar una nueva carpeta."""
        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        if folder_name:
            new_folder = {"title": folder_name, "is_folder": True, "contents": [], "color": "white"}
            if self.current_folder is None:
                self.notes.append(new_folder)
            else:
                self.current_folder['contents'].append(new_folder)
            self.load_notes_list(self.current_folder)
            save_notes(self.notes)

    def delete_note_or_folder(self):
        """Eliminar la nota o carpeta seleccionada."""
        selection = self.notes_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if self.current_folder is None:
            item_list = self.notes
        else:
            item_list = self.current_folder['contents']

        if messagebox.askyesno("Delete", f"Are you sure you want to delete '{item_list[index]['title']}'?"):
            del item_list[index]
            self.load_notes_list(self.current_folder)
            save_notes(self.notes)

    def clear_all_notes(self):
        """Eliminar todas las notas y carpetas."""
        if messagebox.askyesno("Delete All", "Are you sure you want to delete all notes and folders?"):
            self.notes.clear()
            self.load_notes_list()
            save_notes(self.notes)
            messagebox.showinfo("Success", "All notes and folders have been deleted")

    def show_context_menu(self, event):
        """Mostrar el menú contextual al hacer clic derecho."""
        try:
            self.notes_listbox.selection_clear(0, tk.END)
            self.notes_listbox.selection_set(self.notes_listbox.nearest(event.y))
            self.context_menu.post(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def on_closing(self):
        """Guardar las notas y cerrar la aplicación."""
        save_notes(self.notes)
        self.root.destroy()

if __name__ == "__main__":
    try:
        config = load_config()  # Cargar la configuración al iniciar
        root = tk.Tk()
        app = Pynote(root, config)
        root.mainloop()  # Iniciar el bucle principal de la aplicación
    except FileNotFoundError as e:
        print(e)
        messagebox.showerror("Error", f"Error: {e}")